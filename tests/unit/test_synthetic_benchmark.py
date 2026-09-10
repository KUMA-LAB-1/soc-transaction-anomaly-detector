import pytest

from src.synthetic.benchmark import (
    ScenarioSeparationBenchmarkEntry,
    summarize_metric,
    summarize_scenario_separation_comparisons,
)
from src.synthetic.dataset_comparison import ScenarioSeparationComparisonEntry
from src.synthetic.quality import ScenarioSeparationProfile


def test_summarize_metric_reports_variability_across_runs() -> None:
    summary = summarize_metric(
        (
            0.10,
            0.30,
            0.50,
        )
    )

    assert summary.sample_count == 3
    assert summary.mean == pytest.approx(0.30)
    assert summary.standard_deviation == pytest.approx(0.16329931618554522)
    assert summary.minimum == pytest.approx(0.10)
    assert summary.maximum == pytest.approx(0.50)


def test_summarize_metric_ignores_missing_values() -> None:
    summary = summarize_metric(
        (
            0.10,
            None,
            0.50,
        )
    )

    assert summary is not None
    assert summary.sample_count == 2
    assert summary.mean == pytest.approx(0.30)
    assert summary.standard_deviation == pytest.approx(0.20)
    assert summary.minimum == pytest.approx(0.10)
    assert summary.maximum == pytest.approx(0.50)


def test_summarize_metric_returns_none_when_no_values_are_observed() -> None:
    summary = summarize_metric(
        (
            None,
            None,
        )
    )

    assert summary is None


def _comparison_entry(
    *,
    new_device_gap_delta: float | None,
    limit_change_gap_delta: float | None,
    location_change_gap_delta: float | None,
    transaction_value_ecdf_distance_delta: float | None,
    recent_login_failures_ecdf_distance_delta: float | None,
) -> ScenarioSeparationComparisonEntry:
    reference = ScenarioSeparationProfile(
        left_scenario="baseline",
        right_scenario="account_takeover",
        new_device_gap=0.10,
        limit_change_gap=0.20,
        location_change_gap=0.30,
        transaction_value_ecdf_distance=0.40,
        recent_login_failures_ecdf_distance=0.50,
    )

    candidate = ScenarioSeparationProfile(
        left_scenario="baseline",
        right_scenario="account_takeover",
        new_device_gap=0.20,
        limit_change_gap=0.30,
        location_change_gap=0.40,
        transaction_value_ecdf_distance=0.50,
        recent_login_failures_ecdf_distance=0.60,
    )

    return ScenarioSeparationComparisonEntry(
        left_scenario="baseline",
        right_scenario="account_takeover",
        reference=reference,
        candidate=candidate,
        new_device_gap_delta=new_device_gap_delta,
        limit_change_gap_delta=limit_change_gap_delta,
        location_change_gap_delta=location_change_gap_delta,
        transaction_value_ecdf_distance_delta=(transaction_value_ecdf_distance_delta),
        recent_login_failures_ecdf_distance_delta=(
            recent_login_failures_ecdf_distance_delta
        ),
    )


def test_summarize_scenario_separation_comparisons_aggregates_runs_without_judgment() -> (
    None
):
    runs = (
        (
            _comparison_entry(
                new_device_gap_delta=0.10,
                limit_change_gap_delta=-0.20,
                location_change_gap_delta=None,
                transaction_value_ecdf_distance_delta=-0.30,
                recent_login_failures_ecdf_distance_delta=0.40,
            ),
        ),
        (
            _comparison_entry(
                new_device_gap_delta=0.30,
                limit_change_gap_delta=-0.10,
                location_change_gap_delta=None,
                transaction_value_ecdf_distance_delta=-0.50,
                recent_login_failures_ecdf_distance_delta=0.20,
            ),
        ),
    )

    result = summarize_scenario_separation_comparisons(runs)

    assert len(result) == 1

    benchmark = result[0]

    assert isinstance(
        benchmark,
        ScenarioSeparationBenchmarkEntry,
    )

    assert benchmark.left_scenario == "baseline"
    assert benchmark.right_scenario == "account_takeover"

    assert benchmark.new_device_gap_delta is not None
    assert benchmark.new_device_gap_delta.sample_count == 2
    assert benchmark.new_device_gap_delta.mean == pytest.approx(0.20)
    assert benchmark.new_device_gap_delta.standard_deviation == pytest.approx(0.10)
    assert benchmark.new_device_gap_delta.minimum == pytest.approx(0.10)
    assert benchmark.new_device_gap_delta.maximum == pytest.approx(0.30)

    assert benchmark.limit_change_gap_delta is not None
    assert benchmark.limit_change_gap_delta.sample_count == 2
    assert benchmark.limit_change_gap_delta.mean == pytest.approx(-0.15)
    assert benchmark.limit_change_gap_delta.standard_deviation == pytest.approx(0.05)

    assert benchmark.location_change_gap_delta is None

    assert benchmark.transaction_value_ecdf_distance_delta is not None
    assert benchmark.transaction_value_ecdf_distance_delta.sample_count == 2
    assert benchmark.transaction_value_ecdf_distance_delta.mean == pytest.approx(-0.40)
    assert (
        benchmark.transaction_value_ecdf_distance_delta.standard_deviation
        == pytest.approx(0.10)
    )

    assert benchmark.recent_login_failures_ecdf_distance_delta is not None
    assert benchmark.recent_login_failures_ecdf_distance_delta.sample_count == 2
    assert benchmark.recent_login_failures_ecdf_distance_delta.mean == pytest.approx(
        0.30
    )
    assert (
        benchmark.recent_login_failures_ecdf_distance_delta.standard_deviation
        == pytest.approx(0.10)
    )


def _pair_comparison_entry(
    *,
    left_scenario: str,
    right_scenario: str,
    delta: float,
) -> ScenarioSeparationComparisonEntry:
    reference = ScenarioSeparationProfile(
        left_scenario=left_scenario,
        right_scenario=right_scenario,
        new_device_gap=0.10,
        limit_change_gap=0.10,
        location_change_gap=0.10,
        transaction_value_ecdf_distance=0.10,
        recent_login_failures_ecdf_distance=0.10,
    )

    candidate = ScenarioSeparationProfile(
        left_scenario=left_scenario,
        right_scenario=right_scenario,
        new_device_gap=0.10 + delta,
        limit_change_gap=0.10 + delta,
        location_change_gap=0.10 + delta,
        transaction_value_ecdf_distance=0.10 + delta,
        recent_login_failures_ecdf_distance=0.10 + delta,
    )

    return ScenarioSeparationComparisonEntry(
        left_scenario=left_scenario,
        right_scenario=right_scenario,
        reference=reference,
        candidate=candidate,
        new_device_gap_delta=delta,
        limit_change_gap_delta=delta,
        location_change_gap_delta=delta,
        transaction_value_ecdf_distance_delta=delta,
        recent_login_failures_ecdf_distance_delta=delta,
    )


def test_summarize_scenario_separation_comparisons_aligns_pairs_by_identity() -> None:
    runs = (
        (
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="account_takeover",
                delta=0.10,
            ),
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="transaction_anomaly",
                delta=0.20,
            ),
        ),
        (
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="transaction_anomaly",
                delta=0.40,
            ),
            _pair_comparison_entry(
                left_scenario="account_takeover",
                right_scenario="baseline",
                delta=0.30,
            ),
        ),
    )

    result = summarize_scenario_separation_comparisons(runs)

    assert len(result) == 2

    first = result[0]
    second = result[1]

    assert first.left_scenario == "baseline"
    assert first.right_scenario == "account_takeover"
    assert first.new_device_gap_delta is not None
    assert first.new_device_gap_delta.sample_count == 2
    assert first.new_device_gap_delta.mean == pytest.approx(0.20)

    assert second.left_scenario == "baseline"
    assert second.right_scenario == "transaction_anomaly"
    assert second.new_device_gap_delta is not None
    assert second.new_device_gap_delta.sample_count == 2
    assert second.new_device_gap_delta.mean == pytest.approx(0.30)


def test_summarize_scenario_separation_comparisons_rejects_duplicate_pair() -> None:
    runs = (
        (
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="account_takeover",
                delta=0.10,
            ),
        ),
        (
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="account_takeover",
                delta=0.20,
            ),
            _pair_comparison_entry(
                left_scenario="account_takeover",
                right_scenario="baseline",
                delta=0.30,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=("run 2 contem par duplicado: baseline / account_takeover"),
    ):
        summarize_scenario_separation_comparisons(runs)


def test_summarize_scenario_separation_comparisons_rejects_missing_pair() -> None:
    runs = (
        (
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="account_takeover",
                delta=0.10,
            ),
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="transaction_anomaly",
                delta=0.20,
            ),
        ),
        (
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="transaction_anomaly",
                delta=0.30,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "run 2 nao contem par presente no run de referencia: "
            "baseline / account_takeover"
        ),
    ):
        summarize_scenario_separation_comparisons(runs)


def test_summarize_scenario_separation_comparisons_rejects_extra_pair() -> None:
    runs = (
        (
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="account_takeover",
                delta=0.10,
            ),
        ),
        (
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="account_takeover",
                delta=0.20,
            ),
            _pair_comparison_entry(
                left_scenario="baseline",
                right_scenario="transaction_anomaly",
                delta=0.30,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "run 2 contem par ausente no run de referencia: "
            "baseline / transaction_anomaly"
        ),
    ):
        summarize_scenario_separation_comparisons(runs)


def test_summarize_metric_single_observation_has_zero_variability() -> None:
    summary = summarize_metric((0.25,))

    assert summary is not None
    assert summary.sample_count == 1
    assert summary.mean == pytest.approx(0.25)
    assert summary.standard_deviation == pytest.approx(0.0)
    assert summary.minimum == pytest.approx(0.25)
    assert summary.maximum == pytest.approx(0.25)


def test_summarize_scenario_separation_comparisons_returns_empty_for_no_runs() -> None:
    result = summarize_scenario_separation_comparisons(())

    assert result == ()
