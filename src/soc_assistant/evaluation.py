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


@dataclass
class GuardedSocEvaluationSummary:
    evaluation_count: int
    hypothesis_count: int
    unsupported_hypothesis_count: int
    unsupported_claim_rate: float
    confirmation_evaluable_count: int
    false_confirmation_count: int
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


def summarize_guarded_evaluations(
    evaluations: tuple[GuardedSocEvaluation, ...],
) -> GuardedSocEvaluationSummary:
    evaluation_count = len(evaluations)

    hypothesis_count = sum(evaluation.hypothesis_count for evaluation in evaluations)
    unsupported_hypothesis_count = sum(
        evaluation.unsupported_hypothesis_count for evaluation in evaluations
    )
    unsupported_claim_rate = (
        unsupported_hypothesis_count / hypothesis_count if hypothesis_count else 0.0
    )

    evaluable_confirmations = tuple(
        evaluation
        for evaluation in evaluations
        if evaluation.false_confirmation_count is not None
    )
    confirmation_evaluable_count = len(evaluable_confirmations)
    false_confirmation_count = sum(
        evaluation.false_confirmation_count for evaluation in evaluable_confirmations
    )
    false_confirmation_rate = (
        false_confirmation_count / confirmation_evaluable_count
        if confirmation_evaluable_count
        else None
    )

    return GuardedSocEvaluationSummary(
        evaluation_count=evaluation_count,
        hypothesis_count=hypothesis_count,
        unsupported_hypothesis_count=unsupported_hypothesis_count,
        unsupported_claim_rate=unsupported_claim_rate,
        confirmation_evaluable_count=confirmation_evaluable_count,
        false_confirmation_count=false_confirmation_count,
        false_confirmation_rate=false_confirmation_rate,
    )
