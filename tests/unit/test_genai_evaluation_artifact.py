import json

from src.genai.evaluation_artifact import build_evaluation_artifact
from src.genai.evaluation_runner import (
    GenerativeEvaluationExecution,
    GenerativeEvaluationRun,
)
from src.genai.evaluation_summary import summarize_generative_run
from src.genai.response_evaluation import (
    CriterionEvaluation,
    EvaluationVerdict,
    GenerativeResponseEvaluation,
)


def _run():
    evaluation = GenerativeResponseEvaluation(
        case_id="ALT-EVAL-001",
        response_text="Resposta de teste.",
        criteria=(
            CriterionEvaluation(
                name="grounding",
                verdict=EvaluationVerdict.PASS,
                reason="ok",
            ),
            CriterionEvaluation(
                name="coherence",
                verdict=EvaluationVerdict.REVIEW,
                reason="revisão semântica",
            ),
        ),
    )

    return GenerativeEvaluationRun(
        executions=(
            GenerativeEvaluationExecution(
                case_id="ALT-EVAL-001",
                response_text="Resposta de teste.",
                evaluation=evaluation,
            ),
        ),
    )


def test_artefato_preserva_execucoes_metricas_e_metadata():
    run = _run()
    summary = summarize_generative_run(run)

    artifact = build_evaluation_artifact(
        run,
        summary=summary,
        provider="gemini",
        model="gemini-test",
        generated_at="2026-09-20T18:00:00-03:00",
    )

    assert artifact["schema_version"] == 1
    assert artifact["provider"] == "gemini"
    assert artifact["model"] == "gemini-test"
    assert artifact["generated_at"] == "2026-09-20T18:00:00-03:00"

    assert artifact["summary"]["execution_count"] == 1
    assert artifact["summary"]["criterion_count"] == 2
    assert artifact["summary"]["pass_count"] == 1
    assert artifact["summary"]["review_count"] == 1

    assert artifact["executions"][0]["case_id"] == "ALT-EVAL-001"
    assert artifact["executions"][0]["response_text"] == "Resposta de teste."

    criteria = artifact["executions"][0]["criteria"]

    assert criteria[0]["name"] == "grounding"
    assert criteria[0]["verdict"] == "pass"
    assert criteria[1]["verdict"] == "review"


def test_artefato_e_json_serializavel():
    run = _run()
    summary = summarize_generative_run(run)

    artifact = build_evaluation_artifact(
        run,
        summary=summary,
        provider="gemini",
        model="gemini-test",
        generated_at="2026-09-20T18:00:00-03:00",
    )

    serialized = json.dumps(
        artifact,
        ensure_ascii=False,
        sort_keys=True,
    )

    assert "ALT-EVAL-001" in serialized
    assert "Resposta de teste." in serialized


def test_artefato_nao_expoe_segredos():
    run = _run()
    summary = summarize_generative_run(run)

    artifact = build_evaluation_artifact(
        run,
        summary=summary,
        provider="gemini",
        model="gemini-test",
        generated_at="2026-09-20T18:00:00-03:00",
    )

    serialized = json.dumps(artifact)

    assert "api_key" not in serialized.casefold()
    assert "gemini_api_key" not in serialized.casefold()
