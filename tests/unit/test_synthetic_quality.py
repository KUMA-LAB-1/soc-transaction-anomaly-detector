import pytest

from src.synthetic.diagnostics import ScenarioObservableDiagnosticsEntry
from src.synthetic.quality import (
    ScenarioBehaviorSeparationEntry,
    analyze_behavior_flag_separation,
)


def test_analyze_behavior_flag_separation_calcula_gaps_entre_cenarios():
    diagnostics = (
        ScenarioObservableDiagnosticsEntry(
            scenario="baseline",
            record_count=100,
            transaction_value_median=None,
            recent_login_failures_mean=None,
            new_device_proportion=0.10,
            limit_change_proportion=0.20,
            location_change_proportion=0.30,
        ),
        ScenarioObservableDiagnosticsEntry(
            scenario="account_takeover",
            record_count=100,
            transaction_value_median=None,
            recent_login_failures_mean=None,
            new_device_proportion=0.40,
            limit_change_proportion=0.80,
            location_change_proportion=0.50,
        ),
    )

    result = analyze_behavior_flag_separation(diagnostics)

    assert result == (
        ScenarioBehaviorSeparationEntry(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=pytest.approx(0.30),
            limit_change_gap=pytest.approx(0.60),
            location_change_gap=pytest.approx(0.20),
        ),
    )


def test_analyze_behavior_flag_separation_calcula_todos_os_pares():
    diagnostics = (
        ScenarioObservableDiagnosticsEntry(
            scenario="baseline",
            record_count=100,
            transaction_value_median=None,
            recent_login_failures_mean=None,
            new_device_proportion=0.10,
            limit_change_proportion=0.20,
            location_change_proportion=0.30,
        ),
        ScenarioObservableDiagnosticsEntry(
            scenario="account_takeover",
            record_count=100,
            transaction_value_median=None,
            recent_login_failures_mean=None,
            new_device_proportion=0.40,
            limit_change_proportion=0.80,
            location_change_proportion=0.50,
        ),
        ScenarioObservableDiagnosticsEntry(
            scenario="location_anomaly",
            record_count=100,
            transaction_value_median=None,
            recent_login_failures_mean=None,
            new_device_proportion=0.70,
            limit_change_proportion=0.10,
            location_change_proportion=0.90,
        ),
    )

    result = analyze_behavior_flag_separation(diagnostics)

    assert result == (
        ScenarioBehaviorSeparationEntry(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=pytest.approx(0.30),
            limit_change_gap=pytest.approx(0.60),
            location_change_gap=pytest.approx(0.20),
        ),
        ScenarioBehaviorSeparationEntry(
            left_scenario="baseline",
            right_scenario="location_anomaly",
            new_device_gap=pytest.approx(0.60),
            limit_change_gap=pytest.approx(0.10),
            location_change_gap=pytest.approx(0.60),
        ),
        ScenarioBehaviorSeparationEntry(
            left_scenario="account_takeover",
            right_scenario="location_anomaly",
            new_device_gap=pytest.approx(0.30),
            limit_change_gap=pytest.approx(0.70),
            location_change_gap=pytest.approx(0.40),
        ),
    )


def test_analyze_behavior_flag_separation_preserva_gap_indisponivel():
    diagnostics = (
        ScenarioObservableDiagnosticsEntry(
            scenario="baseline",
            record_count=0,
            transaction_value_median=None,
            recent_login_failures_mean=None,
            new_device_proportion=None,
            limit_change_proportion=0.20,
            location_change_proportion=0.30,
        ),
        ScenarioObservableDiagnosticsEntry(
            scenario="account_takeover",
            record_count=100,
            transaction_value_median=None,
            recent_login_failures_mean=None,
            new_device_proportion=0.40,
            limit_change_proportion=None,
            location_change_proportion=0.90,
        ),
    )

    result = analyze_behavior_flag_separation(diagnostics)

    assert result == (
        ScenarioBehaviorSeparationEntry(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=None,
            limit_change_gap=None,
            location_change_gap=pytest.approx(0.60),
        ),
    )
