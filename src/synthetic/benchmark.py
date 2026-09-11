from dataclasses import dataclass
from statistics import fmean, pstdev

from .dataset_comparison import ScenarioSeparationComparisonEntry


@dataclass(frozen=True, slots=True)
class MetricSummary:
    sample_count: int
    mean: float
    standard_deviation: float
    minimum: float
    maximum: float


def summarize_metric(
    values: tuple[float | None, ...],
) -> MetricSummary | None:
    observed_values = tuple(value for value in values if value is not None)

    if not observed_values:
        return None

    return MetricSummary(
        sample_count=len(observed_values),
        mean=fmean(observed_values),
        standard_deviation=pstdev(observed_values),
        minimum=min(observed_values),
        maximum=max(observed_values),
    )


@dataclass(frozen=True, slots=True)
class ScenarioSeparationBenchmarkEntry:
    left_scenario: str
    right_scenario: str
    new_device_gap_delta: MetricSummary | None
    limit_change_gap_delta: MetricSummary | None
    location_change_gap_delta: MetricSummary | None
    transaction_value_ecdf_distance_delta: MetricSummary | None
    recent_login_failures_ecdf_distance_delta: MetricSummary | None


def _scenario_pair_key(
    entry: ScenarioSeparationComparisonEntry,
) -> tuple[str, str]:
    left_scenario, right_scenario = sorted(
        (
            entry.left_scenario,
            entry.right_scenario,
        )
    )

    return left_scenario, right_scenario


def _index_run_pairs(
    run: tuple[ScenarioSeparationComparisonEntry, ...],
    *,
    run_number: int,
) -> dict[
    tuple[str, str],
    ScenarioSeparationComparisonEntry,
]:
    indexed: dict[
        tuple[str, str],
        ScenarioSeparationComparisonEntry,
    ] = {}

    for entry in run:
        pair_key = _scenario_pair_key(entry)

        if pair_key in indexed:
            existing_entry = indexed[pair_key]

            raise ValueError(
                f"run {run_number} contem par duplicado: "
                f"{existing_entry.left_scenario} / "
                f"{existing_entry.right_scenario}"
            )

        indexed[pair_key] = entry

    return indexed


def summarize_scenario_separation_comparisons(
    runs: tuple[
        tuple[ScenarioSeparationComparisonEntry, ...],
        ...,
    ],
) -> tuple[ScenarioSeparationBenchmarkEntry, ...]:
    if not runs:
        return ()

    reference_run = runs[0]

    benchmarks: list[ScenarioSeparationBenchmarkEntry] = []

    indexed_runs = tuple(
        _index_run_pairs(
            run,
            run_number=run_number,
        )
        for run_number, run in enumerate(
            runs,
            start=1,
        )
    )

    reference_index = indexed_runs[0]
    reference_pairs = set(reference_index)

    for run_number, indexed_run in enumerate(
        indexed_runs[1:],
        start=2,
    ):
        run_pairs = set(indexed_run)

        missing_pairs = reference_pairs - run_pairs

        if missing_pairs:
            missing_key = sorted(missing_pairs)[0]
            reference_entry = reference_index[missing_key]

            raise ValueError(
                f"run {run_number} nao contem par presente no run de referencia: "
                f"{reference_entry.left_scenario} / "
                f"{reference_entry.right_scenario}"
            )

        extra_pairs = run_pairs - reference_pairs

        if extra_pairs:
            extra_key = sorted(extra_pairs)[0]
            extra_entry = indexed_run[extra_key]

            raise ValueError(
                f"run {run_number} contem par ausente no run de referencia: "
                f"{extra_entry.left_scenario} / "
                f"{extra_entry.right_scenario}"
            )

    for reference_entry in reference_run:
        pair_key = _scenario_pair_key(reference_entry)

        run_entries = tuple(indexed_run[pair_key] for indexed_run in indexed_runs)

        benchmarks.append(
            ScenarioSeparationBenchmarkEntry(
                left_scenario=reference_entry.left_scenario,
                right_scenario=reference_entry.right_scenario,
                new_device_gap_delta=summarize_metric(
                    tuple(entry.new_device_gap_delta for entry in run_entries)
                ),
                limit_change_gap_delta=summarize_metric(
                    tuple(entry.limit_change_gap_delta for entry in run_entries)
                ),
                location_change_gap_delta=summarize_metric(
                    tuple(entry.location_change_gap_delta for entry in run_entries)
                ),
                transaction_value_ecdf_distance_delta=summarize_metric(
                    tuple(
                        entry.transaction_value_ecdf_distance_delta
                        for entry in run_entries
                    )
                ),
                recent_login_failures_ecdf_distance_delta=summarize_metric(
                    tuple(
                        entry.recent_login_failures_ecdf_distance_delta
                        for entry in run_entries
                    )
                ),
            )
        )

    return tuple(benchmarks)
