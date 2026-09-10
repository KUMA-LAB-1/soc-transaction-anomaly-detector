import pytest

from src.synthetic.dataset_comparison import (
    ScenarioTruthCoverageComparisonEntry,
    compare_scenario_truth_coverage,
    compare_synthetic_dataset_truth_coverage,
)
from src.synthetic.truth_diagnostics import ScenarioTruthCoverageEntry


def test_compare_scenario_truth_coverage_calcula_deltas_candidate_menos_reference():
    reference = (
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=0,
            severity_score_proportion=0.0,
            event_intensity_count=0,
            event_intensity_proportion=0.0,
        ),
    )

    candidate = (
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=100,
            severity_score_proportion=1.0,
            event_intensity_count=80,
            event_intensity_proportion=0.8,
        ),
    )

    result = compare_scenario_truth_coverage(
        reference,
        candidate,
    )

    assert result == (
        ScenarioTruthCoverageComparisonEntry(
            scenario="account_takeover",
            reference=reference[0],
            candidate=candidate[0],
            severity_score_proportion_delta=1.0,
            event_intensity_proportion_delta=0.8,
        ),
    )


def test_compare_scenario_truth_coverage_alinha_cenarios_por_identidade():
    reference = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=20,
            severity_score_proportion=0.20,
            event_intensity_count=10,
            event_intensity_proportion=0.10,
        ),
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=40,
            severity_score_proportion=0.40,
            event_intensity_count=30,
            event_intensity_proportion=0.30,
        ),
    )

    candidate = (
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=80,
            severity_score_proportion=0.80,
            event_intensity_count=70,
            event_intensity_proportion=0.70,
        ),
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=50,
            severity_score_proportion=0.50,
            event_intensity_count=40,
            event_intensity_proportion=0.40,
        ),
    )

    result = compare_scenario_truth_coverage(
        reference,
        candidate,
    )

    assert result[0].scenario == "baseline"
    assert result[0].reference == reference[0]
    assert result[0].candidate == candidate[1]
    assert result[0].severity_score_proportion_delta == pytest.approx(0.30)
    assert result[0].event_intensity_proportion_delta == pytest.approx(0.30)

    assert result[1].scenario == "account_takeover"
    assert result[1].reference == reference[1]
    assert result[1].candidate == candidate[0]
    assert result[1].severity_score_proportion_delta == pytest.approx(0.40)
    assert result[1].event_intensity_proportion_delta == pytest.approx(0.40)


def test_compare_scenario_truth_coverage_rejeita_scenario_duplicado_no_candidate():
    reference = (
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=20,
            severity_score_proportion=0.20,
            event_intensity_count=10,
            event_intensity_proportion=0.10,
        ),
    )

    candidate = (
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=50,
            severity_score_proportion=0.50,
            event_intensity_count=40,
            event_intensity_proportion=0.40,
        ),
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=80,
            severity_score_proportion=0.80,
            event_intensity_count=70,
            event_intensity_proportion=0.70,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("candidate contem scenario duplicado: account_takeover"),
    ):
        compare_scenario_truth_coverage(
            reference,
            candidate,
        )


def test_compare_scenario_truth_coverage_rejeita_scenario_duplicado_em_reference():
    reference = (
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=20,
            severity_score_proportion=0.20,
            event_intensity_count=10,
            event_intensity_proportion=0.10,
        ),
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=40,
            severity_score_proportion=0.40,
            event_intensity_count=30,
            event_intensity_proportion=0.30,
        ),
    )

    candidate = (
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=80,
            severity_score_proportion=0.80,
            event_intensity_count=70,
            event_intensity_proportion=0.70,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("reference contem scenario duplicado: account_takeover"),
    ):
        compare_scenario_truth_coverage(
            reference,
            candidate,
        )


def test_compare_scenario_truth_coverage_rejeita_scenario_de_reference_ausente_no_candidate():
    reference = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=20,
            severity_score_proportion=0.20,
            event_intensity_count=10,
            event_intensity_proportion=0.10,
        ),
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=40,
            severity_score_proportion=0.40,
            event_intensity_count=30,
            event_intensity_proportion=0.30,
        ),
    )

    candidate = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=50,
            severity_score_proportion=0.50,
            event_intensity_count=40,
            event_intensity_proportion=0.40,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("candidate nao contem scenario presente em reference: account_takeover"),
    ):
        compare_scenario_truth_coverage(
            reference,
            candidate,
        )


def test_compare_scenario_truth_coverage_rejeita_scenario_do_candidate_ausente_em_reference():
    reference = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=20,
            severity_score_proportion=0.20,
            event_intensity_count=10,
            event_intensity_proportion=0.10,
        ),
    )

    candidate = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=50,
            severity_score_proportion=0.50,
            event_intensity_count=40,
            event_intensity_proportion=0.40,
        ),
        ScenarioTruthCoverageEntry(
            scenario="account_takeover",
            record_count=100,
            severity_score_count=80,
            severity_score_proportion=0.80,
            event_intensity_count=70,
            event_intensity_proportion=0.70,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("candidate contem scenario ausente em reference: account_takeover"),
    ):
        compare_scenario_truth_coverage(
            reference,
            candidate,
        )


def test_compare_scenario_truth_coverage_preserva_delta_indisponivel():
    reference = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=0,
            severity_score_count=0,
            severity_score_proportion=None,
            event_intensity_count=0,
            event_intensity_proportion=None,
        ),
    )

    candidate = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=100,
            severity_score_proportion=1.0,
            event_intensity_count=50,
            event_intensity_proportion=0.50,
        ),
    )

    result = compare_scenario_truth_coverage(
        reference,
        candidate,
    )

    assert result[0].severity_score_proportion_delta is None
    assert result[0].event_intensity_proportion_delta is None


def test_compare_synthetic_dataset_truth_coverage_reutiliza_diagnosticos_causais(
    monkeypatch,
):
    import src.synthetic.dataset_comparison as dataset_comparison

    reference_dataset = object()
    candidate_dataset = object()

    reference_coverage = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=0,
            severity_score_proportion=0.0,
            event_intensity_count=0,
            event_intensity_proportion=0.0,
        ),
    )

    candidate_coverage = (
        ScenarioTruthCoverageEntry(
            scenario="baseline",
            record_count=100,
            severity_score_count=100,
            severity_score_proportion=1.0,
            event_intensity_count=50,
            event_intensity_proportion=0.50,
        ),
    )

    chamadas = []

    def fake_analyze_scenario_truth_coverage(dataset):
        chamadas.append(dataset)

        if dataset is reference_dataset:
            return reference_coverage

        if dataset is candidate_dataset:
            return candidate_coverage

        raise AssertionError("dataset inesperado")

    monkeypatch.setattr(
        dataset_comparison,
        "analyze_scenario_truth_coverage",
        fake_analyze_scenario_truth_coverage,
    )

    result = compare_synthetic_dataset_truth_coverage(
        reference_dataset,
        candidate_dataset,
    )

    assert chamadas == [
        reference_dataset,
        candidate_dataset,
    ]

    assert result == compare_scenario_truth_coverage(
        reference_coverage,
        candidate_coverage,
    )
