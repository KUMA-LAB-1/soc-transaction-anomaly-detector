from dataclasses import dataclass

from .assessment import GuardedSocAssessment


@dataclass
class GuardedSocEvaluation:
    alert_id: str
    hypothesis_count: int
    unsupported_hypothesis_count: int
    unsupported_claim_rate: float


def evaluate_guarded_assessment(
    assessment: GuardedSocAssessment,
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

    return GuardedSocEvaluation(
        alert_id=assessment.alert_id,
        hypothesis_count=hypothesis_count,
        unsupported_hypothesis_count=unsupported_hypothesis_count,
        unsupported_claim_rate=unsupported_claim_rate,
    )
