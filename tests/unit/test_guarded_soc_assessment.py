from datetime import UTC, datetime

from src.alerts.engine import criar_alerta
from src.evidence_context import build_evidence_context
from src.soc_assistant.assessment import build_guarded_assessment


def test_guarded_assessment_preserva_identidade_e_lacunas_conhecidas():
    registro = {
        "id_transacao": 101,
        "cliente_pseudonimo": "cliente-01",
        "data_hora_transacao": datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
        "tipo_transacao": "Pix",
        "valor_transacao": 5000.0,
        "proba_suspeita": 0.90,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.42,
        "score_risco_predito": 92.0,
        "falhas_login_recentes": 4,
        "dispositivo_novo_flag": True,
        "alteracao_limite_flag": False,
        "mudanca_localizacao_flag": False,
    }

    alerta = criar_alerta(
        registro,
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
        },
        alert_id="ALT-GUARDED-001",
        created_at=datetime(2026, 8, 18, 13, 0, tzinfo=UTC),
    )

    contexto = build_evidence_context(alerta)

    assessment = build_guarded_assessment(contexto)

    assert assessment.alert_id == contexto.alert_id
    assert assessment.missing_evidence == contexto.quality.missing_evidence
