from dataclasses import dataclass

from .assessment import GuardedSocAssessment


@dataclass
class GuardedSocEvaluation:
    alert_id: str
    hypothesis_count: int
    unsupported_hypothesis_count: int
    unsupported_claim_rate: float
    false_confirmation_count: int | None
    false_confirmation_rate: float | None


def evaluate_guarded_assessment(
    assessment: GuardedSocAssessment,
    *,
    expected_incident_confirmed: bool | None = None,
) -> GuardedSocEvaluation:
    observed_fact_names = {fact.name for fact in assessment.facts}

    unsupported_hypothesis_count = sum(
        not set(hypothesis.supporting_fact_names).issubset(observed_fact_names)
        for hypothesis in assessment.hypotheses
    )

    hypothesis_count = len(assessment.hypotheses)

    unsupported_claim_rate = (
        unsupported_hypothesis_count / hypothesis_count if hypothesis_count else 0.0
    )

    if expected_incident_confirmed is None:
        false_confirmation_count = None
        false_confirmation_rate = None
    else:
        false_confirmation_count = int(
            assessment.incident_confirmed and not expected_incident_confirmed
        )
        false_confirmation_rate = float(false_confirmation_count)

    return GuardedSocEvaluation(
        alert_id=assessment.alert_id,
        hypothesis_count=hypothesis_count,
        unsupported_hypothesis_count=unsupported_hypothesis_count,
        unsupported_claim_rate=unsupported_claim_rate,
        false_confirmation_count=false_confirmation_count,
        false_confirmation_rate=false_confirmation_rate,
    )
