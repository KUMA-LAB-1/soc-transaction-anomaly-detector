from collections import Counter
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .dataset import GeneratedSyntheticDataset


@dataclass(frozen=True, slots=True)
class ScenarioTruthCoverageEntry:
    scenario: str
    record_count: int
    severity_score_count: int
    severity_score_proportion: float | None
    event_intensity_count: int
    event_intensity_proportion: float | None


def _optional_proportion(
    count: int,
    total: int,
) -> float | None:
    if total == 0:
        return None

    return count / total


def analyze_scenario_truth_coverage(
    dataset: "GeneratedSyntheticDataset",
) -> tuple[ScenarioTruthCoverageEntry, ...]:
    scenarios = tuple(
        dict.fromkeys(entry.scenario for entry in dataset.manifest.scenarios)
    )

    manifest_scenarios = set(scenarios)
    record_scenarios = {record.truth.scenario for record in dataset.records}

    undeclared_scenarios = record_scenarios - manifest_scenarios

    if undeclared_scenarios:
        undeclared_scenario = sorted(undeclared_scenarios)[0]

        raise ValueError(
            f"records contem scenario ausente do manifest: {undeclared_scenario}"
        )

    record_counts = Counter(record.truth.scenario for record in dataset.records)

    severity_counts = Counter(
        record.truth.scenario
        for record in dataset.records
        if record.truth.severity_score is not None
    )

    intensity_counts = Counter(
        record.truth.scenario
        for record in dataset.records
        if record.truth.event_intensity is not None
    )

    return tuple(
        ScenarioTruthCoverageEntry(
            scenario=scenario,
            record_count=record_counts[scenario],
            severity_score_count=severity_counts[scenario],
            severity_score_proportion=_optional_proportion(
                severity_counts[scenario],
                record_counts[scenario],
            ),
            event_intensity_count=intensity_counts[scenario],
            event_intensity_proportion=_optional_proportion(
                intensity_counts[scenario],
                record_counts[scenario],
            ),
        )
        for scenario in scenarios
    )
