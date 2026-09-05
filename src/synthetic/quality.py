from dataclasses import dataclass
from itertools import combinations

import numpy as np

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


def empirical_cdf_distance(
    left: tuple[float, ...],
    right: tuple[float, ...],
) -> float:
    left_values = np.sort(np.asarray(left, dtype=float))
    right_values = np.sort(np.asarray(right, dtype=float))

    if left_values.size == 0 or right_values.size == 0:
        raise ValueError("amostras não podem ser vazias.")

    if not np.isfinite(left_values).all() or not np.isfinite(right_values).all():
        raise ValueError("amostras devem conter apenas valores finitos.")

    points = np.unique(
        np.concatenate(
            (
                left_values,
                right_values,
            )
        )
    )

    left_ecdf = (
        np.searchsorted(
            left_values,
            points,
            side="right",
        )
        / left_values.size
    )
    right_ecdf = (
        np.searchsorted(
            right_values,
            points,
            side="right",
        )
        / right_values.size
    )

    return float(np.max(np.abs(left_ecdf - right_ecdf)))
