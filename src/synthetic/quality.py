from dataclasses import dataclass
from itertools import combinations
from typing import TYPE_CHECKING

import numpy as np

from .diagnostics import ScenarioObservableDiagnosticsEntry
from .observables import (
    get_recent_login_failures,
    get_transaction_value,
)

if TYPE_CHECKING:
    from .dataset import GeneratedSyntheticDataset


@dataclass(frozen=True, slots=True)
class ScenarioBehaviorSeparationEntry:
    left_scenario: str
    right_scenario: str
    new_device_gap: float | None
    limit_change_gap: float | None
    location_change_gap: float | None


@dataclass(frozen=True, slots=True)
class ScenarioDistributionSeparationEntry:
    left_scenario: str
    right_scenario: str
    transaction_value_ecdf_distance: float | None
    recent_login_failures_ecdf_distance: float | None


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


def _optional_ecdf_distance(
    left: tuple[float, ...],
    right: tuple[float, ...],
) -> float | None:
    if not left or not right:
        return None

    return empirical_cdf_distance(left, right)


def analyze_scenario_distribution_separation(
    dataset: "GeneratedSyntheticDataset",
) -> tuple[ScenarioDistributionSeparationEntry, ...]:
    scenarios = tuple(
        dict.fromkeys(entry.scenario for entry in dataset.manifest.scenarios)
    )

    transaction_values_by_scenario: dict[str, list[float]] = {
        scenario: [] for scenario in scenarios
    }

    login_failures_by_scenario: dict[str, list[int]] = {
        scenario: [] for scenario in scenarios
    }

    for record in dataset.records:
        scenario = record.truth.scenario

        if scenario not in transaction_values_by_scenario:
            raise ValueError("cenário observado não está presente no manifest")

        transaction_values_by_scenario[scenario].append(
            get_transaction_value(record.observables)
        )
        login_failures_by_scenario[scenario].append(
            get_recent_login_failures(record.observables)
        )

    return tuple(
        ScenarioDistributionSeparationEntry(
            left_scenario=left_scenario,
            right_scenario=right_scenario,
            transaction_value_ecdf_distance=_optional_ecdf_distance(
                tuple(transaction_values_by_scenario[left_scenario]),
                tuple(transaction_values_by_scenario[right_scenario]),
            ),
            recent_login_failures_ecdf_distance=_optional_ecdf_distance(
                tuple(login_failures_by_scenario[left_scenario]),
                tuple(login_failures_by_scenario[right_scenario]),
            ),
        )
        for left_scenario, right_scenario in combinations(scenarios, 2)
    )
