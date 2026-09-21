from __future__ import annotations

from dataclasses import dataclass

from src.genai.contracts import LlmAdapter
from src.genai.conversation import ConversationService
from src.genai.evaluation_cases import GenerativeEvaluationCase
from src.genai.response_evaluation import (
    GenerativeResponseEvaluation,
    evaluate_generative_response,
)


@dataclass(frozen=True)
class GenerativeEvaluationExecution:
    case_id: str
    response_text: str
    evaluation: GenerativeResponseEvaluation


@dataclass(frozen=True)
class GenerativeEvaluationRun:
    executions: tuple[GenerativeEvaluationExecution, ...]


def run_generative_evaluation(
    adapter: LlmAdapter,
    *,
    cases: tuple[GenerativeEvaluationCase, ...],
) -> GenerativeEvaluationRun:
    """Executa casos generativos pelo fluxo real de conversa e os avalia."""

    conversation = ConversationService(adapter)

    executions = []

    for case in cases:
        response = conversation.ask(
            case.assessment,
            user_message=case.user_message,
        )

        evaluation = evaluate_generative_response(
            case,
            response.content,
        )

        executions.append(
            GenerativeEvaluationExecution(
                case_id=case.case_id,
                response_text=response.content,
                evaluation=evaluation,
            )
        )

    return GenerativeEvaluationRun(
        executions=tuple(executions),
    )
