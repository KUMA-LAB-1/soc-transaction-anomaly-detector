from __future__ import annotations

from typing import Any

from src.genai.evaluation_runner import GenerativeEvaluationRun
from src.genai.evaluation_summary import GenerativeEvaluationSummary


def build_evaluation_artifact(
    run: GenerativeEvaluationRun,
    *,
    summary: GenerativeEvaluationSummary,
    provider: str,
    model: str,
    generated_at: str,
) -> dict[str, Any]:
    """Projeta uma execução generativa em artefato JSON-safe e auditável."""

    return {
        "schema_version": 1,
        "provider": provider,
        "model": model,
        "generated_at": generated_at,
        "summary": {
            "execution_count": summary.execution_count,
            "criterion_count": summary.criterion_count,
            "pass_count": summary.pass_count,
            "fail_count": summary.fail_count,
            "review_count": summary.review_count,
            "automated_decision_count": summary.automated_decision_count,
            "automated_pass_rate": summary.automated_pass_rate,
            "review_rate": summary.review_rate,
            "by_criterion": [
                {
                    "name": item.name,
                    "total_count": item.total_count,
                    "pass_count": item.pass_count,
                    "fail_count": item.fail_count,
                    "review_count": item.review_count,
                }
                for item in summary.by_criterion
            ],
        },
        "executions": [
            {
                "case_id": execution.case_id,
                "response_text": execution.response_text,
                "criteria": [
                    {
                        "name": criterion.name,
                        "verdict": criterion.verdict.value,
                        "reason": criterion.reason,
                    }
                    for criterion in execution.evaluation.criteria
                ],
            }
            for execution in run.executions
        ],
    }
