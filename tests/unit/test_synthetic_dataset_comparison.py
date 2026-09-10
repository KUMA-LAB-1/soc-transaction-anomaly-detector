import pytest

from src.synthetic.dataset_comparison import (
    ScenarioSeparationComparisonEntry,
    compare_scenario_separation_profiles,
    compare_synthetic_dataset_scenario_separation,
)
from src.synthetic.quality import ScenarioSeparationProfile


def test_compare_scenario_separation_profiles_calcula_deltas_sem_julgamento():
    reference = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.10,
            limit_change_gap=0.20,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=0.40,
            recent_login_failures_ecdf_distance=0.50,
        ),
    )

    candidate = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.25,
            limit_change_gap=0.15,
            location_change_gap=0.45,
            transaction_value_ecdf_distance=0.10,
            recent_login_failures_ecdf_distance=0.80,
        ),
    )

    result = compare_scenario_separation_profiles(
        reference,
        candidate,
    )

    assert len(result) == 1

    comparison = result[0]

    assert isinstance(
        comparison,
        ScenarioSeparationComparisonEntry,
    )

    assert comparison.left_scenario == "baseline"
    assert comparison.right_scenario == "account_takeover"

    assert comparison.reference == reference[0]
    assert comparison.candidate == candidate[0]

    assert comparison.new_device_gap_delta == pytest.approx(0.15)
    assert comparison.limit_change_gap_delta == pytest.approx(-0.05)
    assert comparison.location_change_gap_delta == pytest.approx(0.15)
    assert comparison.transaction_value_ecdf_distance_delta == pytest.approx(-0.30)
    assert comparison.recent_login_failures_ecdf_distance_delta == pytest.approx(0.30)


def test_compare_scenario_separation_profiles_preserva_delta_indisponivel():
    reference = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=None,
            limit_change_gap=0.40,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=None,
            recent_login_failures_ecdf_distance=0.50,
        ),
    )

    candidate = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.20,
            limit_change_gap=None,
            location_change_gap=0.10,
            transaction_value_ecdf_distance=None,
            recent_login_failures_ecdf_distance=0.20,
        ),
    )

    result = compare_scenario_separation_profiles(
        reference,
        candidate,
    )

    comparison = result[0]

    assert comparison.new_device_gap_delta is None
    assert comparison.limit_change_gap_delta is None
    assert comparison.location_change_gap_delta == pytest.approx(-0.20)
    assert comparison.transaction_value_ecdf_distance_delta is None
    assert comparison.recent_login_failures_ecdf_distance_delta == pytest.approx(-0.30)


def test_compare_scenario_separation_profiles_alinha_pares_por_identidade():
    reference = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.10,
            limit_change_gap=0.10,
            location_change_gap=0.10,
            transaction_value_ecdf_distance=0.10,
            recent_login_failures_ecdf_distance=0.10,
        ),
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="transaction_anomaly",
            new_device_gap=0.20,
            limit_change_gap=0.20,
            location_change_gap=0.20,
            transaction_value_ecdf_distance=0.20,
            recent_login_failures_ecdf_distance=0.20,
        ),
    )

    candidate = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="transaction_anomaly",
            new_device_gap=0.30,
            limit_change_gap=0.30,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=0.30,
            recent_login_failures_ecdf_distance=0.30,
        ),
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.40,
            limit_change_gap=0.40,
            location_change_gap=0.40,
            transaction_value_ecdf_distance=0.40,
            recent_login_failures_ecdf_distance=0.40,
        ),
    )

    result = compare_scenario_separation_profiles(
        reference,
        candidate,
    )

    assert result[0].reference == reference[0]
    assert result[0].candidate == candidate[1]
    assert result[0].new_device_gap_delta == pytest.approx(0.30)

    assert result[1].reference == reference[1]
    assert result[1].candidate == candidate[0]
    assert result[1].new_device_gap_delta == pytest.approx(0.10)


def test_compare_scenario_separation_profiles_rejeita_par_de_reference_ausente_no_candidate():
    reference = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.10,
            limit_change_gap=0.10,
            location_change_gap=0.10,
            transaction_value_ecdf_distance=0.10,
            recent_login_failures_ecdf_distance=0.10,
        ),
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="transaction_anomaly",
            new_device_gap=0.20,
            limit_change_gap=0.20,
            location_change_gap=0.20,
            transaction_value_ecdf_distance=0.20,
            recent_login_failures_ecdf_distance=0.20,
        ),
    )

    candidate = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.30,
            limit_change_gap=0.30,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=0.30,
            recent_login_failures_ecdf_distance=0.30,
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "candidate nao contem par presente em reference: "
            "baseline / transaction_anomaly"
        ),
    ):
        compare_scenario_separation_profiles(
            reference,
            candidate,
        )


def test_compare_scenario_separation_profiles_rejeita_par_duplicado_no_candidate():
    reference = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.10,
            limit_change_gap=0.10,
            location_change_gap=0.10,
            transaction_value_ecdf_distance=0.10,
            recent_login_failures_ecdf_distance=0.10,
        ),
    )

    candidate = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.20,
            limit_change_gap=0.20,
            location_change_gap=0.20,
            transaction_value_ecdf_distance=0.20,
            recent_login_failures_ecdf_distance=0.20,
        ),
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.30,
            limit_change_gap=0.30,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=0.30,
            recent_login_failures_ecdf_distance=0.30,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("candidate contem par duplicado: baseline / account_takeover"),
    ):
        compare_scenario_separation_profiles(
            reference,
            candidate,
        )


def test_compare_scenario_separation_profiles_rejeita_par_duplicado_em_reference():
    reference = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.10,
            limit_change_gap=0.10,
            location_change_gap=0.10,
            transaction_value_ecdf_distance=0.10,
            recent_login_failures_ecdf_distance=0.10,
        ),
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.20,
            limit_change_gap=0.20,
            location_change_gap=0.20,
            transaction_value_ecdf_distance=0.20,
            recent_login_failures_ecdf_distance=0.20,
        ),
    )

    candidate = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.30,
            limit_change_gap=0.30,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=0.30,
            recent_login_failures_ecdf_distance=0.30,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("reference contem par duplicado: baseline / account_takeover"),
    ):
        compare_scenario_separation_profiles(
            reference,
            candidate,
        )


def test_compare_scenario_separation_profiles_rejeita_par_do_candidate_ausente_em_reference():
    reference = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.10,
            limit_change_gap=0.10,
            location_change_gap=0.10,
            transaction_value_ecdf_distance=0.10,
            recent_login_failures_ecdf_distance=0.10,
        ),
    )

    candidate = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.20,
            limit_change_gap=0.20,
            location_change_gap=0.20,
            transaction_value_ecdf_distance=0.20,
            recent_login_failures_ecdf_distance=0.20,
        ),
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="transaction_anomaly",
            new_device_gap=0.30,
            limit_change_gap=0.30,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=0.30,
            recent_login_failures_ecdf_distance=0.30,
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "candidate contem par ausente em reference: baseline / transaction_anomaly"
        ),
    ):
        compare_scenario_separation_profiles(
            reference,
            candidate,
        )


def test_compare_scenario_separation_profiles_aceita_mesmo_par_com_orientacao_invertida():
    reference = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.10,
            limit_change_gap=0.20,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=0.40,
            recent_login_failures_ecdf_distance=0.50,
        ),
    )

    candidate = (
        ScenarioSeparationProfile(
            left_scenario="account_takeover",
            right_scenario="baseline",
            new_device_gap=0.30,
            limit_change_gap=0.40,
            location_change_gap=0.50,
            transaction_value_ecdf_distance=0.60,
            recent_login_failures_ecdf_distance=0.70,
        ),
    )

    result = compare_scenario_separation_profiles(
        reference,
        candidate,
    )

    assert len(result) == 1

    comparison = result[0]

    assert comparison.left_scenario == "baseline"
    assert comparison.right_scenario == "account_takeover"

    assert comparison.reference == reference[0]
    assert comparison.candidate == candidate[0]

    assert comparison.new_device_gap_delta == pytest.approx(0.20)
    assert comparison.limit_change_gap_delta == pytest.approx(0.20)
    assert comparison.location_change_gap_delta == pytest.approx(0.20)
    assert comparison.transaction_value_ecdf_distance_delta == pytest.approx(0.20)
    assert comparison.recent_login_failures_ecdf_distance_delta == pytest.approx(0.20)


def test_compare_synthetic_dataset_scenario_separation_reutiliza_perfis_de_separacao(
    monkeypatch,
):
    import src.synthetic.dataset_comparison as dataset_comparison

    reference_dataset = object()
    candidate_dataset = object()

    reference_profiles = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.10,
            limit_change_gap=0.20,
            location_change_gap=0.30,
            transaction_value_ecdf_distance=0.40,
            recent_login_failures_ecdf_distance=0.50,
        ),
    )

    candidate_profiles = (
        ScenarioSeparationProfile(
            left_scenario="baseline",
            right_scenario="account_takeover",
            new_device_gap=0.30,
            limit_change_gap=0.40,
            location_change_gap=0.50,
            transaction_value_ecdf_distance=0.60,
            recent_login_failures_ecdf_distance=0.70,
        ),
    )

    chamadas = []

    def fake_analyze_scenario_separation_profile(dataset):
        chamadas.append(dataset)

        if dataset is reference_dataset:
            return reference_profiles

        if dataset is candidate_dataset:
            return candidate_profiles

        raise AssertionError("dataset inesperado")

    monkeypatch.setattr(
        dataset_comparison,
        "analyze_scenario_separation_profile",
        fake_analyze_scenario_separation_profile,
    )

    result = compare_synthetic_dataset_scenario_separation(
        reference_dataset,
        candidate_dataset,
    )

    assert chamadas == [
        reference_dataset,
        candidate_dataset,
    ]

    assert result == compare_scenario_separation_profiles(
        reference_profiles,
        candidate_profiles,
    )
