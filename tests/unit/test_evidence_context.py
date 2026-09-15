from datetime import UTC, datetime

from src.alerts.engine import criar_alerta
from src.evidence_context import build_evidence_context


def criar_registro():
    return {
        "id_transacao": 101,
        "cliente_pseudonimo": "cliente-01",
        "data_hora_transacao": datetime(
            2026,
            8,
            18,
            12,
            0,
            tzinfo=UTC,
        ),
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


def test_build_evidence_context_preserva_evidencia_nao_observada():
    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
        },
        alert_id="ALT-EVIDENCE-001",
        created_at=datetime(
            2026,
            8,
            18,
            13,
            0,
            tzinfo=UTC,
        ),
    )

    contexto = build_evidence_context(alerta)

    assert contexto.evidence.limit_change.value is False
    assert contexto.evidence.limit_change.observed is False
    assert contexto.evidence.location_change.value is False
    assert contexto.evidence.location_change.observed is False
    assert contexto.quality.missing_evidence == (
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    )
