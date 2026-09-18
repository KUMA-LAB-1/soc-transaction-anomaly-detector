from src.soc_assistant.assessment import (
    GuardedSocAssessment,
    ObservedFact,
    SupportedHypothesis,
)
from src.soc_assistant.evaluation import (
    GuardedSocEvaluation,
    GuardedSocEvaluationScenario,
    evaluate_guarded_assessment,
    evaluate_guarded_matrix,
    summarize_guarded_evaluations,
)


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


def test_evaluator_detecta_confirmacao_falsa_contra_truth_externa():
    assessment = GuardedSocAssessment(
        alert_id="ALT-EVAL-CONFIRM-001",
        missing_evidence=(),
        facts=(
            ObservedFact(
                name="failed_logins",
                value=8,
            ),
        ),
        hypotheses=(
            SupportedHypothesis(
                statement="possible_account_compromise",
                supporting_fact_names=("failed_logins",),
            ),
        ),
        recommended_checks=(),
        incident_confirmed=True,
    )

    evaluation = evaluate_guarded_assessment(
        assessment,
        expected_incident_confirmed=False,
    )

    assert evaluation.false_confirmation_count == 1
    assert evaluation.false_confirmation_rate == 1.0


def test_evaluator_nao_marca_falsa_confirmacao_quando_truth_confirma_incidente():
    assessment = GuardedSocAssessment(
        alert_id="ALT-EVAL-CONFIRM-002",
        missing_evidence=(),
        facts=(),
        hypotheses=(),
        recommended_checks=(),
        incident_confirmed=True,
    )

    evaluation = evaluate_guarded_assessment(
        assessment,
        expected_incident_confirmed=True,
    )

    assert evaluation.false_confirmation_count == 0
    assert evaluation.false_confirmation_rate == 0.0


def test_evaluator_nao_marca_falsa_confirmacao_quando_assistant_nao_confirma():
    assessment = GuardedSocAssessment(
        alert_id="ALT-EVAL-CONFIRM-003",
        missing_evidence=(),
        facts=(),
        hypotheses=(),
        recommended_checks=(),
        incident_confirmed=False,
    )

    evaluation = evaluate_guarded_assessment(
        assessment,
        expected_incident_confirmed=False,
    )

    assert evaluation.false_confirmation_count == 0
    assert evaluation.false_confirmation_rate == 0.0


def test_evaluator_mantem_confirmacao_nao_avaliada_sem_truth_externa():
    assessment = GuardedSocAssessment(
        alert_id="ALT-EVAL-CONFIRM-004",
        missing_evidence=(),
        facts=(),
        hypotheses=(),
        recommended_checks=(),
        incident_confirmed=False,
    )

    evaluation = evaluate_guarded_assessment(assessment)

    assert evaluation.false_confirmation_count is None
    assert evaluation.false_confirmation_rate is None


def test_summary_agrega_metricas_sem_contar_truth_ausente_no_denominador():
    evaluations = (
        GuardedSocEvaluation(
            alert_id="ALT-MATRIX-001",
            hypothesis_count=2,
            unsupported_hypothesis_count=1,
            unsupported_claim_rate=0.5,
            false_confirmation_count=1,
            false_confirmation_rate=1.0,
        ),
        GuardedSocEvaluation(
            alert_id="ALT-MATRIX-002",
            hypothesis_count=1,
            unsupported_hypothesis_count=0,
            unsupported_claim_rate=0.0,
            false_confirmation_count=0,
            false_confirmation_rate=0.0,
        ),
        GuardedSocEvaluation(
            alert_id="ALT-MATRIX-003",
            hypothesis_count=0,
            unsupported_hypothesis_count=0,
            unsupported_claim_rate=0.0,
            false_confirmation_count=None,
            false_confirmation_rate=None,
        ),
    )

    summary = summarize_guarded_evaluations(evaluations)

    assert summary.evaluation_count == 3

    assert summary.hypothesis_count == 3
    assert summary.unsupported_hypothesis_count == 1
    assert summary.unsupported_claim_rate == 1 / 3

    assert summary.confirmation_evaluable_count == 2
    assert summary.false_confirmation_count == 1
    assert summary.false_confirmation_rate == 0.5


def test_summary_vazio_nao_fabrica_metricas():
    summary = summarize_guarded_evaluations(())

    assert summary.evaluation_count == 0
    assert summary.hypothesis_count == 0
    assert summary.unsupported_hypothesis_count == 0
    assert summary.unsupported_claim_rate == 0.0

    assert summary.confirmation_evaluable_count == 0
    assert summary.false_confirmation_count == 0
    assert summary.false_confirmation_rate is None


def test_summary_sem_truth_disponivel_mantem_taxa_de_confirmacao_nao_avaliada():
    evaluations = (
        GuardedSocEvaluation(
            alert_id="ALT-MATRIX-NO-TRUTH-001",
            hypothesis_count=1,
            unsupported_hypothesis_count=0,
            unsupported_claim_rate=0.0,
            false_confirmation_count=None,
            false_confirmation_rate=None,
        ),
        GuardedSocEvaluation(
            alert_id="ALT-MATRIX-NO-TRUTH-002",
            hypothesis_count=2,
            unsupported_hypothesis_count=1,
            unsupported_claim_rate=0.5,
            false_confirmation_count=None,
            false_confirmation_rate=None,
        ),
    )

    summary = summarize_guarded_evaluations(evaluations)

    assert summary.evaluation_count == 2

    assert summary.hypothesis_count == 3
    assert summary.unsupported_hypothesis_count == 1
    assert summary.unsupported_claim_rate == 1 / 3

    assert summary.confirmation_evaluable_count == 0
    assert summary.false_confirmation_count == 0
    assert summary.false_confirmation_rate is None


def test_matrix_avalia_cenarios_e_entrega_evaluations_com_summary():
    scenario_false_confirmation = GuardedSocEvaluationScenario(
        assessment=GuardedSocAssessment(
            alert_id="ALT-MATRIX-RUN-001",
            missing_evidence=(),
            facts=(
                ObservedFact(
                    name="failed_logins",
                    value=12,
                ),
            ),
            hypotheses=(
                SupportedHypothesis(
                    statement="possible_account_compromise",
                    supporting_fact_names=("failed_logins",),
                ),
            ),
            recommended_checks=(),
            incident_confirmed=True,
        ),
        expected_incident_confirmed=False,
    )

    scenario_without_truth = GuardedSocEvaluationScenario(
        assessment=GuardedSocAssessment(
            alert_id="ALT-MATRIX-RUN-002",
            missing_evidence=(),
            facts=(),
            hypotheses=(),
            recommended_checks=(),
            incident_confirmed=False,
        ),
        expected_incident_confirmed=None,
    )

    matrix = evaluate_guarded_matrix(
        (
            scenario_false_confirmation,
            scenario_without_truth,
        )
    )

    assert len(matrix.evaluations) == 2

    assert matrix.evaluations[0].alert_id == "ALT-MATRIX-RUN-001"
    assert matrix.evaluations[0].false_confirmation_count == 1

    assert matrix.evaluations[1].alert_id == "ALT-MATRIX-RUN-002"
    assert matrix.evaluations[1].false_confirmation_count is None

    assert matrix.summary.evaluation_count == 2
    assert matrix.summary.hypothesis_count == 1
    assert matrix.summary.unsupported_hypothesis_count == 0
    assert matrix.summary.unsupported_claim_rate == 0.0
    assert matrix.summary.confirmation_evaluable_count == 1
    assert matrix.summary.false_confirmation_count == 1
    assert matrix.summary.false_confirmation_rate == 1.0


def test_matrix_vazia_retorna_evaluations_e_summary_vazios():
    matrix = evaluate_guarded_matrix(())

    assert matrix.evaluations == ()

    assert matrix.summary.evaluation_count == 0
    assert matrix.summary.hypothesis_count == 0
    assert matrix.summary.unsupported_hypothesis_count == 0
    assert matrix.summary.unsupported_claim_rate == 0.0
    assert matrix.summary.confirmation_evaluable_count == 0
    assert matrix.summary.false_confirmation_count == 0
    assert matrix.summary.false_confirmation_rate is None
