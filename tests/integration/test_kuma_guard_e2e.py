from datetime import UTC, datetime

import pytest

from src.alerts.engine import criar_alerta
from src.evidence_context import build_evidence_context
from src.soc_assistant.assessment import (
    add_supported_hypothesis,
    build_guarded_assessment,
)
from src.soc_assistant.evaluation import (
    GuardedSocEvaluationScenario,
    evaluate_guarded_matrix,
)


@pytest.mark.integration
def test_alert_evidence_guard_and_evaluation_matrix_preservam_contrato_defensivo():
    registro = {
        "id_transacao": 901,
        "cliente_pseudonimo": "cliente-e2e-01",
        "data_hora_transacao": datetime(
            2026,
            9,
            18,
            18,
            0,
            tzinfo=UTC,
        ),
        "tipo_transacao": "Pix",
        "valor_transacao": 7200.0,
        "proba_suspeita": 0.96,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.71,
        "score_risco_predito": 94.0,
        "falhas_login_recentes": 5,
        "dispositivo_novo_flag": True,
        "alteracao_limite_flag": False,
        "mudanca_localizacao_flag": False,
    }

    alert = criar_alerta(
        registro,
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
        },
        alert_id="ALT-KUMA-GUARD-E2E-001",
        created_at=datetime(
            2026,
            9,
            18,
            18,
            5,
            tzinfo=UTC,
        ),
    )

    context = build_evidence_context(alert)

    assessment = build_guarded_assessment(context)

    add_supported_hypothesis(
        assessment,
        statement="possible_account_compromise",
        supporting_fact_names=(
            "failed_logins",
            "new_device",
        ),
    )

    matrix = evaluate_guarded_matrix(
        (
            GuardedSocEvaluationScenario(
                assessment=assessment,
                expected_incident_confirmed=False,
            ),
        )
    )

    assert context.alert_id == alert.alert_id
    assert context.source_schema_version == alert.schema_version

    assert tuple(fact.name for fact in assessment.facts) == (
        "failed_logins",
        "new_device",
    )
    assert assessment.missing_evidence == (
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    )
    assert (
        tuple(check.evidence_name for check in assessment.recommended_checks)
        == assessment.missing_evidence
    )

    assert len(assessment.hypotheses) == 1
    assert assessment.hypotheses[0].supporting_fact_names == (
        "failed_logins",
        "new_device",
    )
    assert assessment.incident_confirmed is False

    assert len(matrix.evaluations) == 1

    evaluation = matrix.evaluations[0]

    assert evaluation.alert_id == alert.alert_id
    assert evaluation.hypothesis_count == 1
    assert evaluation.unsupported_hypothesis_count == 0
    assert evaluation.unsupported_claim_rate == 0.0
    assert evaluation.false_confirmation_count == 0
    assert evaluation.false_confirmation_rate == 0.0

    assert matrix.summary.evaluation_count == 1
    assert matrix.summary.hypothesis_count == 1
    assert matrix.summary.unsupported_hypothesis_count == 0
    assert matrix.summary.unsupported_claim_rate == 0.0
    assert matrix.summary.confirmation_evaluable_count == 1
    assert matrix.summary.false_confirmation_count == 0
    assert matrix.summary.false_confirmation_rate == 0.0
