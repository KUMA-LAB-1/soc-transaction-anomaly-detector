from datetime import datetime

from src.synthetic.benchmark_harness import (
    run_synthetic_scenario_separation_benchmark,
)
from src.synthetic.composer import ScenarioMix
from src.synthetic.generation_config import SyntheticGenerationConfig
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.manifest import DatasetManifestV2
from src.synthetic.scenarios import obter_cenario
from src.synthetic.seed_strategy import build_synthetic_seed_plan


def test_synthetic_benchmark_harness_preserves_real_seed_provenance() -> None:
    seeds = (11, 29)

    inicio = datetime(2026, 1, 1)
    fim = datetime(2026, 1, 2)

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=0.5,
        ),
        ScenarioMix(
            cenario=obter_cenario("account_takeover"),
            proporcao=0.5,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    generation_config = SyntheticGenerationConfig()

    result = run_synthetic_scenario_separation_benchmark(
        seeds=seeds,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    assert tuple(run.seed for run in result.runs) == seeds

    for run, seed in zip(
        result.runs,
        seeds,
        strict=True,
    ):
        assert run.reference_manifest.seed == seed
        assert run.candidate_manifest.seed == seed

        assert run.reference_manifest.quantidade == 40
        assert run.candidate_manifest.quantidade == 40

        assert run.reference_manifest.inicio == inicio
        assert run.candidate_manifest.inicio == inicio

        assert run.reference_manifest.fim == fim
        assert run.candidate_manifest.fim == fim

        assert run.reference_manifest.scenarios == run.candidate_manifest.scenarios
        assert (
            run.reference_manifest.label_policy == run.candidate_manifest.label_policy
        )

        assert run.reference_manifest.schema_version == "1"

        assert isinstance(
            run.candidate_manifest,
            DatasetManifestV2,
        )
        assert run.candidate_manifest.schema_version == "2"

        expected_seed_plan = build_synthetic_seed_plan(seed)

        seed_strategy = run.candidate_manifest.generation.seed_strategy

        assert seed_strategy.statistical_seed == expected_seed_plan.statistical_seed
        assert seed_strategy.population_seed == expected_seed_plan.population_seed

        assert len(run.comparisons) == 1

        comparison = run.comparisons[0]

        assert comparison.left_scenario == "baseline"
        assert comparison.right_scenario == "account_takeover"

    assert len(result.summary) == 1

    summary = result.summary[0]

    assert summary.left_scenario == "baseline"
    assert summary.right_scenario == "account_takeover"

    metrics = (
        summary.new_device_gap_delta,
        summary.limit_change_gap_delta,
        summary.location_change_gap_delta,
        summary.transaction_value_ecdf_distance_delta,
        summary.recent_login_failures_ecdf_distance_delta,
    )

    for metric in metrics:
        assert metric is not None
        assert metric.sample_count == len(seeds)
