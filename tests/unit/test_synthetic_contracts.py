import pytest

from src.synthetic.contracts import GenerationTruth


def test_generation_truth_aceita_severity_score_explicito():
    truth = GenerationTruth(
        scenario="account_takeover",
        is_suspicious=True,
        attack_profile="account_takeover",
        expected_mitre_techniques=("T1098",),
        severity_score=72.5,
    )

    assert truth.severity_score == 72.5


def test_generation_truth_severity_score_padrao_e_none():
    truth = GenerationTruth(
        scenario="baseline",
        is_suspicious=False,
    )

    assert truth.severity_score is None


@pytest.mark.parametrize(
    "severity_score",
    [
        -0.01,
        100.01,
        float("inf"),
        float("-inf"),
        float("nan"),
        True,
        "72.5",
    ],
)
def test_generation_truth_rejeita_severity_score_invalido(severity_score):
    with pytest.raises(
        ValueError,
        match="severity_score",
    ):
        GenerationTruth(
            scenario="account_takeover",
            is_suspicious=True,
            severity_score=severity_score,
        )


@pytest.mark.parametrize("severity_score", [0.0, 100.0])
def test_generation_truth_aceita_limites_de_severity_score(severity_score):
    truth = GenerationTruth(
        scenario="baseline",
        is_suspicious=False,
        severity_score=severity_score,
    )

    assert truth.severity_score == severity_score


def test_generation_truth_aceita_event_intensity_explicita():
    truth = GenerationTruth(
        scenario="account_takeover",
        is_suspicious=True,
        event_intensity=0.65,
    )

    assert truth.event_intensity == 0.65


def test_generation_truth_event_intensity_padrao_e_none():
    truth = GenerationTruth(
        scenario="baseline",
        is_suspicious=False,
    )

    assert truth.event_intensity is None


@pytest.mark.parametrize(
    "event_intensity",
    [
        -0.01,
        1.01,
        float("inf"),
        float("-inf"),
        float("nan"),
        True,
        "0.65",
    ],
)
def test_generation_truth_rejeita_event_intensity_invalida(event_intensity):
    with pytest.raises(
        ValueError,
        match="event_intensity",
    ):
        GenerationTruth(
            scenario="account_takeover",
            is_suspicious=True,
            event_intensity=event_intensity,
        )


@pytest.mark.parametrize(
    "event_intensity",
    [
        0.0,
        1.0,
    ],
)
def test_generation_truth_aceita_limites_de_event_intensity(event_intensity):
    truth = GenerationTruth(
        scenario="baseline",
        is_suspicious=False,
        event_intensity=event_intensity,
    )

    assert truth.event_intensity == event_intensity


def test_generation_truth_valida_event_intensity_sem_severity_score():
    with pytest.raises(
        ValueError,
        match="event_intensity",
    ):
        GenerationTruth(
            scenario="account_takeover",
            is_suspicious=True,
            severity_score=None,
            event_intensity=1.01,
        )
