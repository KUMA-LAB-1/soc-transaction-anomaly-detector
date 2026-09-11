from datetime import datetime

from .behavior_flags import BehaviorFlagBaseline
from .benchmark import MetricSummary, summarize_metric
from .benchmark_harness import (
    ScenarioSeparationBenchmarkResult,
    ScenarioSeparationBenchmarkRun,
    run_synthetic_scenario_separation_benchmark,
)
from .composer import ScenarioMix
from .dataset_comparison import ScenarioSeparationComparisonEntry
from .generation_config import (
    ScenarioGenerationConfig,
    SyntheticGenerationConfig,
)
from .intensity import EventIntensityPolicy
from .label_policy import OperationalLabelPolicy
from .population_generation import PopulationGenerationConfig
from .scenario_effect_catalog import obter_efeito_cenario
from .scenarios import obter_cenario
from .severity import SeverityPolicy

CANONICAL_SEEDS = tuple(range(1, 31))
CANONICAL_QUANTIDADE = 1000
CANONICAL_INICIO = datetime(2026, 1, 1)
CANONICAL_FIM = datetime(2026, 1, 8)

_TARGET_PAIR = frozenset(
    (
        "baseline",
        "account_takeover",
    )
)

_METRICS = (
    (
        "new_device",
        "new_device_gap",
        "new_device_gap_delta",
    ),
    (
        "limit_change",
        "limit_change_gap",
        "limit_change_gap_delta",
    ),
    (
        "location_change",
        "location_change_gap",
        "location_change_gap_delta",
    ),
    (
        "transaction_ecdf",
        "transaction_value_ecdf_distance",
        "transaction_value_ecdf_distance_delta",
    ),
    (
        "login_failures_ecdf",
        "recent_login_failures_ecdf_distance",
        "recent_login_failures_ecdf_distance_delta",
    ),
)


def build_canonical_generation_config() -> SyntheticGenerationConfig:
    baseline = obter_cenario("baseline")

    return SyntheticGenerationConfig(
        population_config=PopulationGenerationConfig(
            customer_count=5,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
            behavior_flag_baseline=BehaviorFlagBaseline(
                new_device_probability=(baseline.probabilidade_dispositivo_novo),
                limit_change_probability=(baseline.probabilidade_alteracao_limite),
                location_change_probability=(
                    baseline.probabilidade_mudanca_localizacao
                ),
            ),
        ),
        severity_policy=SeverityPolicy(
            normal_min=0.0,
            normal_max=40.0,
            suspicious_min=20.0,
            suspicious_max=100.0,
        ),
        scenario_configs=(
            ScenarioGenerationConfig(
                scenario="account_takeover",
                scenario_effect=obter_efeito_cenario("account_takeover"),
                intensity_policy=EventIntensityPolicy(
                    intensity_min=0.20,
                    intensity_max=0.80,
                ),
            ),
        ),
    )


def build_canonical_misturas() -> list[ScenarioMix]:
    return [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=0.50,
        ),
        ScenarioMix(
            cenario=obter_cenario("account_takeover"),
            proporcao=0.50,
        ),
    ]


def build_canonical_label_policy() -> OperationalLabelPolicy:
    return OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )


def run_canonical_scenario_separation_benchmark() -> ScenarioSeparationBenchmarkResult:
    return run_synthetic_scenario_separation_benchmark(
        seeds=CANONICAL_SEEDS,
        quantidade=CANONICAL_QUANTIDADE,
        inicio=CANONICAL_INICIO,
        fim=CANONICAL_FIM,
        misturas=build_canonical_misturas(),
        label_policy=build_canonical_label_policy(),
        generation_config=build_canonical_generation_config(),
    )


def _comparison_for_target_pair(
    run: ScenarioSeparationBenchmarkRun,
) -> ScenarioSeparationComparisonEntry:
    matches = tuple(
        entry
        for entry in run.comparisons
        if frozenset(
            (
                entry.left_scenario,
                entry.right_scenario,
            )
        )
        == _TARGET_PAIR
    )

    if len(matches) != 1:
        raise ValueError(
            "cada run deve conter exatamente uma comparacao "
            "baseline / account_takeover."
        )

    return matches[0]


def _require_summary(
    values: tuple[float | None, ...],
    *,
    metric_name: str,
    side: str,
) -> MetricSummary:
    summary = summarize_metric(values)

    if summary is None:
        raise ValueError(f"{metric_name}/{side} nao possui valores observados.")

    return summary


def _format_summary_line(
    *,
    label: str,
    side: str,
    summary: MetricSummary,
) -> str:
    return (
        f"{label:20s} | "
        f"{side:9s} | "
        f"{summary.sample_count:2d} | "
        f"{summary.mean:+.4f} | "
        f"{summary.standard_deviation:.4f} | "
        f"{summary.minimum:+.4f} | "
        f"{summary.maximum:+.4f}"
    )


def render_benchmark_report(
    result: ScenarioSeparationBenchmarkResult,
) -> str:
    comparisons = tuple(_comparison_for_target_pair(run) for run in result.runs)

    baseline = obter_cenario("baseline")

    lines = [
        "=== CANONICAL SCENARIO SEPARATION BENCHMARK ===",
        "",
        f"root_seeds: {CANONICAL_SEEDS[0]}..{CANONICAL_SEEDS[-1]}",
        f"run_count: {len(result.runs)}",
        f"quantidade_por_run: {CANONICAL_QUANTIDADE}",
        f"inicio: {CANONICAL_INICIO.isoformat()}",
        f"fim: {CANONICAL_FIM.isoformat()}",
        "scenario_mix: baseline=0.50, account_takeover=0.50",
        "customer_count: 5",
        (
            "behavior_flag_baseline: "
            f"new_device={baseline.probabilidade_dispositivo_novo:.4f}, "
            f"limit_change={baseline.probabilidade_alteracao_limite:.4f}, "
            f"location_change={baseline.probabilidade_mudanca_localizacao:.4f}"
        ),
        "account_takeover_intensity: 0.20..0.80",
        "scenario_effect: account_takeover catalog",
        "",
        "metric               | side      |  n | mean    | std    | min     | max",
    ]

    for label, profile_attr, delta_attr in _METRICS:
        reference_values = tuple(
            getattr(entry.reference, profile_attr) for entry in comparisons
        )
        candidate_values = tuple(
            getattr(entry.candidate, profile_attr) for entry in comparisons
        )
        delta_values = tuple(getattr(entry, delta_attr) for entry in comparisons)

        for side, values in (
            ("reference", reference_values),
            ("candidate", candidate_values),
            ("delta", delta_values),
        ):
            summary = _require_summary(
                values,
                metric_name=label,
                side=side,
            )

            lines.append(
                _format_summary_line(
                    label=label,
                    side=side,
                    summary=summary,
                )
            )

        observed_deltas = tuple(value for value in delta_values if value is not None)

        epsilon = 1e-12

        positive = sum(value > epsilon for value in observed_deltas)
        negative = sum(value < -epsilon for value in observed_deltas)
        zero = sum(abs(value) <= epsilon for value in observed_deltas)

        lines.append(
            f"{'':20s} | signs     | "
            f"{positive} positive / "
            f"{negative} negative / "
            f"{zero} zero"
        )
        lines.append("")

    return "\n".join(lines).rstrip()


def main() -> None:
    result = run_canonical_scenario_separation_benchmark()

    print(render_benchmark_report(result))


if __name__ == "__main__":
    main()
