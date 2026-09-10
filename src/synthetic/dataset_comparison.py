from dataclasses import dataclass
from typing import TYPE_CHECKING

from .quality import (
    ScenarioSeparationProfile,
    analyze_scenario_separation_profile,
)
from .truth_diagnostics import (
    ScenarioTruthCoverageEntry,
    analyze_scenario_truth_coverage,
)

if TYPE_CHECKING:
    from .dataset import GeneratedSyntheticDataset


@dataclass(frozen=True, slots=True)
class ScenarioSeparationComparisonEntry:
    left_scenario: str
    right_scenario: str
    reference: ScenarioSeparationProfile
    candidate: ScenarioSeparationProfile
    new_device_gap_delta: float | None
    limit_change_gap_delta: float | None
    location_change_gap_delta: float | None
    transaction_value_ecdf_distance_delta: float | None
    recent_login_failures_ecdf_distance_delta: float | None


def _optional_delta(
    reference: float | None,
    candidate: float | None,
) -> float | None:
    if reference is None or candidate is None:
        return None

    return candidate - reference


def _scenario_pair_key(
    left_scenario: str,
    right_scenario: str,
) -> tuple[str, str]:
    return tuple(sorted((left_scenario, right_scenario)))


def compare_scenario_separation_profiles(
    reference: tuple[ScenarioSeparationProfile, ...],
    candidate: tuple[ScenarioSeparationProfile, ...],
) -> tuple[ScenarioSeparationComparisonEntry, ...]:
    candidate_by_pair: dict[
        tuple[str, str],
        ScenarioSeparationProfile,
    ] = {}

    for entry in candidate:
        pair = (
            entry.left_scenario,
            entry.right_scenario,
        )
        pair_key = _scenario_pair_key(*pair)

        if pair_key in candidate_by_pair:
            raise ValueError(f"candidate contem par duplicado: {pair[0]} / {pair[1]}")

        candidate_by_pair[pair_key] = entry

    comparisons: list[ScenarioSeparationComparisonEntry] = []
    reference_pairs: set[tuple[str, str]] = set()

    for reference_entry in reference:
        pair = (
            reference_entry.left_scenario,
            reference_entry.right_scenario,
        )
        pair_key = _scenario_pair_key(*pair)

        if pair_key in reference_pairs:
            raise ValueError(f"reference contem par duplicado: {pair[0]} / {pair[1]}")

        reference_pairs.add(pair_key)

        if pair_key not in candidate_by_pair:
            raise ValueError(
                f"candidate nao contem par presente em reference: {pair[0]} / {pair[1]}"
            )

        candidate_entry = candidate_by_pair[pair_key]

        comparisons.append(
            ScenarioSeparationComparisonEntry(
                left_scenario=reference_entry.left_scenario,
                right_scenario=reference_entry.right_scenario,
                reference=reference_entry,
                candidate=candidate_entry,
                new_device_gap_delta=_optional_delta(
                    reference_entry.new_device_gap,
                    candidate_entry.new_device_gap,
                ),
                limit_change_gap_delta=_optional_delta(
                    reference_entry.limit_change_gap,
                    candidate_entry.limit_change_gap,
                ),
                location_change_gap_delta=_optional_delta(
                    reference_entry.location_change_gap,
                    candidate_entry.location_change_gap,
                ),
                transaction_value_ecdf_distance_delta=_optional_delta(
                    reference_entry.transaction_value_ecdf_distance,
                    candidate_entry.transaction_value_ecdf_distance,
                ),
                recent_login_failures_ecdf_distance_delta=_optional_delta(
                    reference_entry.recent_login_failures_ecdf_distance,
                    candidate_entry.recent_login_failures_ecdf_distance,
                ),
            )
        )

    extra_candidate_pairs = set(candidate_by_pair) - reference_pairs

    if extra_candidate_pairs:
        extra_key = sorted(extra_candidate_pairs)[0]
        extra_entry = candidate_by_pair[extra_key]

        raise ValueError(
            "candidate contem par ausente em reference: "
            f"{extra_entry.left_scenario} / "
            f"{extra_entry.right_scenario}"
        )

    return tuple(comparisons)


def compare_synthetic_dataset_scenario_separation(
    reference: "GeneratedSyntheticDataset",
    candidate: "GeneratedSyntheticDataset",
) -> tuple[ScenarioSeparationComparisonEntry, ...]:
    reference_profiles = analyze_scenario_separation_profile(reference)
    candidate_profiles = analyze_scenario_separation_profile(candidate)

    return compare_scenario_separation_profiles(
        reference_profiles,
        candidate_profiles,
    )


@dataclass(frozen=True, slots=True)
class ScenarioTruthCoverageComparisonEntry:
    scenario: str
    reference: ScenarioTruthCoverageEntry
    candidate: ScenarioTruthCoverageEntry
    severity_score_proportion_delta: float | None
    event_intensity_proportion_delta: float | None


def compare_scenario_truth_coverage(
    reference: tuple[ScenarioTruthCoverageEntry, ...],
    candidate: tuple[ScenarioTruthCoverageEntry, ...],
) -> tuple[ScenarioTruthCoverageComparisonEntry, ...]:
    candidate_by_scenario: dict[
        str,
        ScenarioTruthCoverageEntry,
    ] = {}

    for entry in candidate:
        if entry.scenario in candidate_by_scenario:
            raise ValueError(f"candidate contem scenario duplicado: {entry.scenario}")

        candidate_by_scenario[entry.scenario] = entry

    comparisons: list[ScenarioTruthCoverageComparisonEntry] = []
    reference_scenarios: set[str] = set()

    for reference_entry in reference:
        if reference_entry.scenario in reference_scenarios:
            raise ValueError(
                f"reference contem scenario duplicado: {reference_entry.scenario}"
            )

        reference_scenarios.add(reference_entry.scenario)

        if reference_entry.scenario not in candidate_by_scenario:
            raise ValueError(
                "candidate nao contem scenario presente em reference: "
                f"{reference_entry.scenario}"
            )

        candidate_entry = candidate_by_scenario[reference_entry.scenario]

        comparisons.append(
            ScenarioTruthCoverageComparisonEntry(
                scenario=reference_entry.scenario,
                reference=reference_entry,
                candidate=candidate_entry,
                severity_score_proportion_delta=_optional_delta(
                    reference_entry.severity_score_proportion,
                    candidate_entry.severity_score_proportion,
                ),
                event_intensity_proportion_delta=_optional_delta(
                    reference_entry.event_intensity_proportion,
                    candidate_entry.event_intensity_proportion,
                ),
            )
        )

    extra_candidate_scenarios = set(candidate_by_scenario) - reference_scenarios

    if extra_candidate_scenarios:
        extra_scenario = sorted(extra_candidate_scenarios)[0]

        raise ValueError(
            f"candidate contem scenario ausente em reference: {extra_scenario}"
        )

    return tuple(comparisons)


def compare_synthetic_dataset_truth_coverage(
    reference: "GeneratedSyntheticDataset",
    candidate: "GeneratedSyntheticDataset",
) -> tuple[ScenarioTruthCoverageComparisonEntry, ...]:
    reference_coverage = analyze_scenario_truth_coverage(reference)
    candidate_coverage = analyze_scenario_truth_coverage(candidate)

    return compare_scenario_truth_coverage(
        reference_coverage,
        candidate_coverage,
    )
