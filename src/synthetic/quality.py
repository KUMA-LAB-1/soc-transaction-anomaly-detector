from dataclasses import dataclass
from itertools import combinations

from .diagnostics import ScenarioObservableDiagnosticsEntry


@dataclass(frozen=True, slots=True)
class ScenarioBehaviorSeparationEntry:
    left_scenario: str
    right_scenario: str
    new_device_gap: float | None
    limit_change_gap: float | None
    location_change_gap: float | None


def _absolute_gap(
    left: float | None,
    right: float | None,
) -> float | None:
    if left is None or right is None:
        return None

    return abs(left - right)


def analyze_behavior_flag_separation(
    diagnostics: tuple[ScenarioObservableDiagnosticsEntry, ...],
) -> tuple[ScenarioBehaviorSeparationEntry, ...]:
    return tuple(
        ScenarioBehaviorSeparationEntry(
            left_scenario=left.scenario,
            right_scenario=right.scenario,
            new_device_gap=_absolute_gap(
                left.new_device_proportion,
                right.new_device_proportion,
            ),
            limit_change_gap=_absolute_gap(
                left.limit_change_proportion,
                right.limit_change_proportion,
            ),
            location_change_gap=_absolute_gap(
                left.location_change_proportion,
                right.location_change_proportion,
            ),
        )
        for left, right in combinations(diagnostics, 2)
    )
