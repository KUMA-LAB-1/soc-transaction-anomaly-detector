from src.soc_assistant.assessment import (
    GuardedSocAssessment,
    ObservedFact,
    SupportedHypothesis,
)
from src.soc_assistant.evaluation import evaluate_guarded_assessment


def test_evaluator_mede_taxa_de_hipoteses_sem_suporte_observado():
    assessment = GuardedSocAssessment(
        alert_id="ALT-EVAL-001",
        missing_evidence=(),
        facts=(
            ObservedFact(
                name="failed_logins",
                value=5,
            ),
        ),
        hypotheses=(
            SupportedHypothesis(
                statement="possible_brute_force",
                supporting_fact_names=("failed_logins",),
            ),
            SupportedHypothesis(
                statement="possible_location_anomaly",
                supporting_fact_names=("location_change",),
            ),
        ),
        recommended_checks=(),
        incident_confirmed=False,
    )

    evaluation = evaluate_guarded_assessment(assessment)

    assert evaluation.alert_id == "ALT-EVAL-001"
    assert evaluation.hypothesis_count == 2
    assert evaluation.unsupported_hypothesis_count == 1
    assert evaluation.unsupported_claim_rate == 0.5
