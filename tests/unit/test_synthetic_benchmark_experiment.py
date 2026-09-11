from types import SimpleNamespace

import src.synthetic.benchmark_experiment as benchmark_experiment
from src.synthetic.behavior_flags import BehaviorFlagBaseline
from src.synthetic.scenario_effect_catalog import obter_efeito_cenario
from src.synthetic.scenarios import obter_cenario


def test_canonical_experiment_preserva_configuracao_validada_do_3n():
    assert benchmark_experiment.CANONICAL_SEEDS == tuple(range(1, 31))
    assert benchmark_experiment.CANONICAL_QUANTIDADE == 1000

    config = benchmark_experiment.build_canonical_generation_config()

    population_config = config.population_config

    assert population_config is not None
    assert population_config.customer_count == 5
    assert population_config.transaction_value_median_base == 180.0
    assert population_config.transaction_value_median_log_sigma == 0.75
    assert population_config.transaction_value_sigma == 0.65
    assert population_config.recent_login_failure_rate_mean == 0.15
    assert population_config.recent_login_failure_rate_shape == 2.0

    baseline = obter_cenario("baseline")

    assert population_config.behavior_flag_baseline == (
        BehaviorFlagBaseline(
            new_device_probability=(baseline.probabilidade_dispositivo_novo),
            limit_change_probability=(baseline.probabilidade_alteracao_limite),
            location_change_probability=(baseline.probabilidade_mudanca_localizacao),
        )
    )

    assert len(config.scenario_configs) == 1

    scenario_config = config.scenario_configs[0]

    assert scenario_config.scenario == "account_takeover"
    assert scenario_config.scenario_effect == obter_efeito_cenario("account_takeover")

    assert scenario_config.intensity_policy is not None
    assert scenario_config.intensity_policy.intensity_min == 0.20
    assert scenario_config.intensity_policy.intensity_max == 0.80


def test_canonical_runner_encaminha_parametros_ao_harness(
    monkeypatch,
):
    captured = {}
    expected_result = object()

    def fake_run(**kwargs):
        captured.update(kwargs)
        return expected_result

    monkeypatch.setattr(
        benchmark_experiment,
        "run_synthetic_scenario_separation_benchmark",
        fake_run,
    )

    result = benchmark_experiment.run_canonical_scenario_separation_benchmark()

    assert result is expected_result

    assert captured["seeds"] == tuple(range(1, 31))
    assert captured["quantidade"] == 1000
    assert captured["inicio"] == benchmark_experiment.CANONICAL_INICIO
    assert captured["fim"] == benchmark_experiment.CANONICAL_FIM

    misturas = captured["misturas"]

    assert len(misturas) == 2
    assert misturas[0].cenario.name == "baseline"
    assert misturas[0].proporcao == 0.50
    assert misturas[1].cenario.name == "account_takeover"
    assert misturas[1].proporcao == 0.50

    label_policy = captured["label_policy"]

    assert label_policy.probabilidade_falso_positivo == 0.0
    assert label_policy.probabilidade_falso_negativo == 0.0


def _comparison(
    *,
    reference_offset: float,
    candidate_offset: float,
):
    reference = SimpleNamespace(
        new_device_gap=0.64 + reference_offset,
        limit_change_gap=0.54 + reference_offset,
        location_change_gap=0.39 + reference_offset,
        transaction_value_ecdf_distance=0.74 + reference_offset,
        recent_login_failures_ecdf_distance=0.42 + reference_offset,
    )
    candidate = SimpleNamespace(
        new_device_gap=0.32 + candidate_offset,
        limit_change_gap=0.27 + candidate_offset,
        location_change_gap=0.20 + candidate_offset,
        transaction_value_ecdf_distance=0.12 + candidate_offset,
        recent_login_failures_ecdf_distance=0.14 + candidate_offset,
    )

    return SimpleNamespace(
        left_scenario="baseline",
        right_scenario="account_takeover",
        reference=reference,
        candidate=candidate,
        new_device_gap_delta=(candidate.new_device_gap - reference.new_device_gap),
        limit_change_gap_delta=(
            candidate.limit_change_gap - reference.limit_change_gap
        ),
        location_change_gap_delta=(
            candidate.location_change_gap - reference.location_change_gap
        ),
        transaction_value_ecdf_distance_delta=(
            candidate.transaction_value_ecdf_distance
            - reference.transaction_value_ecdf_distance
        ),
        recent_login_failures_ecdf_distance_delta=(
            candidate.recent_login_failures_ecdf_distance
            - reference.recent_login_failures_ecdf_distance
        ),
    )


def test_render_benchmark_report_expoe_estabilidade_e_sinais():
    result = SimpleNamespace(
        runs=(
            SimpleNamespace(
                comparisons=(
                    _comparison(
                        reference_offset=0.00,
                        candidate_offset=0.00,
                    ),
                )
            ),
            SimpleNamespace(
                comparisons=(
                    _comparison(
                        reference_offset=0.01,
                        candidate_offset=-0.01,
                    ),
                )
            ),
        )
    )

    report = benchmark_experiment.render_benchmark_report(result)

    assert "CANONICAL SCENARIO SEPARATION BENCHMARK" in report
    assert "root_seeds: 1..30" in report
    assert "run_count: 2" in report
    assert "behavior_flag_baseline:" in report

    for metric in (
        "new_device",
        "limit_change",
        "location_change",
        "transaction_ecdf",
        "login_failures_ecdf",
    ):
        assert metric in report

    assert report.count("0 positive / 2 negative / 0 zero") == 5
