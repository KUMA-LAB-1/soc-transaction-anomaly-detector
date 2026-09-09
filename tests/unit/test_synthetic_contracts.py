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
