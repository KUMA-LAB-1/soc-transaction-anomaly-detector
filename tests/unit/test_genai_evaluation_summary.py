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


def _execution(case_id, criteria):
    return GenerativeEvaluationExecution(
        case_id=case_id,
        response_text="resposta",
        evaluation=GenerativeResponseEvaluation(
            case_id=case_id,
            response_text="resposta",
            criteria=criteria,
        ),
    )


def test_summary_separa_pass_fail_e_review():
    run = GenerativeEvaluationRun(
        executions=(
            _execution(
                "ALT-EVAL-001",
                (
                    CriterionEvaluation(
                        name="grounding",
                        verdict=EvaluationVerdict.PASS,
                        reason="ok",
                    ),
                    CriterionEvaluation(
                        name="coherence",
                        verdict=EvaluationVerdict.REVIEW,
                        reason="manual",
                    ),
                ),
            ),
            _execution(
                "ALT-EVAL-002",
                (
                    CriterionEvaluation(
                        name="non_hallucination",
                        verdict=EvaluationVerdict.FAIL,
                        reason="inventou dado",
                    ),
                ),
            ),
        ),
    )

    summary = summarize_generative_run(run)

    assert summary.execution_count == 2
    assert summary.criterion_count == 3
    assert summary.pass_count == 1
    assert summary.fail_count == 1
    assert summary.review_count == 1


def test_summary_calcula_taxa_apenas_sobre_decisoes_automaticas():
    run = GenerativeEvaluationRun(
        executions=(
            _execution(
                "ALT-EVAL-001",
                (
                    CriterionEvaluation(
                        name="grounding",
                        verdict=EvaluationVerdict.PASS,
                        reason="ok",
                    ),
                    CriterionEvaluation(
                        name="coherence",
                        verdict=EvaluationVerdict.REVIEW,
                        reason="manual",
                    ),
                    CriterionEvaluation(
                        name="authority_preservation",
                        verdict=EvaluationVerdict.FAIL,
                        reason="falha",
                    ),
                ),
            ),
        ),
    )

    summary = summarize_generative_run(run)

    assert summary.automated_decision_count == 2
    assert summary.automated_pass_rate == 0.5
    assert summary.review_rate == 1 / 3


def test_summary_agrega_resultados_por_criterio():
    run = GenerativeEvaluationRun(
        executions=(
            _execution(
                "ALT-EVAL-001",
                (
                    CriterionEvaluation(
                        name="grounding",
                        verdict=EvaluationVerdict.PASS,
                        reason="ok",
                    ),
                    CriterionEvaluation(
                        name="coherence",
                        verdict=EvaluationVerdict.REVIEW,
                        reason="manual",
                    ),
                ),
            ),
            _execution(
                "ALT-EVAL-002",
                (
                    CriterionEvaluation(
                        name="grounding",
                        verdict=EvaluationVerdict.PASS,
                        reason="ok",
                    ),
                    CriterionEvaluation(
                        name="coherence",
                        verdict=EvaluationVerdict.REVIEW,
                        reason="manual",
                    ),
                ),
            ),
        ),
    )

    summary = summarize_generative_run(run)

    grounding = next(item for item in summary.by_criterion if item.name == "grounding")
    coherence = next(item for item in summary.by_criterion if item.name == "coherence")

    assert grounding.total_count == 2
    assert grounding.pass_count == 2
    assert grounding.fail_count == 0
    assert grounding.review_count == 0

    assert coherence.total_count == 2
    assert coherence.pass_count == 0
    assert coherence.fail_count == 0
    assert coherence.review_count == 2
