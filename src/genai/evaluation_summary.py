from __future__ import annotations

from dataclasses import dataclass

from src.genai.evaluation_runner import GenerativeEvaluationRun
from src.genai.response_evaluation import EvaluationVerdict


@dataclass(frozen=True)
class CriterionSummary:
    name: str
    total_count: int
    pass_count: int
    fail_count: int
    review_count: int


@dataclass(frozen=True)
class GenerativeEvaluationSummary:
    execution_count: int
    criterion_count: int
    pass_count: int
    fail_count: int
    review_count: int
    automated_decision_count: int
    automated_pass_rate: float | None
    review_rate: float
    by_criterion: tuple[CriterionSummary, ...]


def summarize_generative_run(
    run: GenerativeEvaluationRun,
) -> GenerativeEvaluationSummary:
    """Resume resultados automáticos sem tratar REVIEW como aprovação."""

    criteria = tuple(
        criterion
        for execution in run.executions
        for criterion in execution.evaluation.criteria
    )

    pass_count = sum(
        criterion.verdict is EvaluationVerdict.PASS for criterion in criteria
    )
    fail_count = sum(
        criterion.verdict is EvaluationVerdict.FAIL for criterion in criteria
    )
    review_count = sum(
        criterion.verdict is EvaluationVerdict.REVIEW for criterion in criteria
    )

    criterion_count = len(criteria)
    automated_decision_count = pass_count + fail_count

    automated_pass_rate = (
        pass_count / automated_decision_count if automated_decision_count else None
    )

    review_rate = review_count / criterion_count if criterion_count else 0.0

    criterion_names = tuple(dict.fromkeys(criterion.name for criterion in criteria))

    by_criterion = tuple(
        CriterionSummary(
            name=name,
            total_count=sum(criterion.name == name for criterion in criteria),
            pass_count=sum(
                criterion.name == name and criterion.verdict is EvaluationVerdict.PASS
                for criterion in criteria
            ),
            fail_count=sum(
                criterion.name == name and criterion.verdict is EvaluationVerdict.FAIL
                for criterion in criteria
            ),
            review_count=sum(
                criterion.name == name and criterion.verdict is EvaluationVerdict.REVIEW
                for criterion in criteria
            ),
        )
        for name in criterion_names
    )

    return GenerativeEvaluationSummary(
        execution_count=len(run.executions),
        criterion_count=criterion_count,
        pass_count=pass_count,
        fail_count=fail_count,
        review_count=review_count,
        automated_decision_count=automated_decision_count,
        automated_pass_rate=automated_pass_rate,
        review_rate=review_rate,
        by_criterion=by_criterion,
    )
