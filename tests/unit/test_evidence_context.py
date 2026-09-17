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


def test_build_evidence_context_preserva_identidade_da_origem():
    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        alert_id="ALT-EVIDENCE-TRACE-001",
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

    assert contexto.alert_id == alerta.alert_id
    assert contexto.source_schema_version == alerta.schema_version


def test_build_evidence_context_preserva_fatos_do_evento():
    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        alert_id="ALT-EVIDENCE-EVENT-001",
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

    assert contexto.event == alerta.event
    assert contexto.event.transaction_id == 101
    assert contexto.event.customer_pseudonym == "cliente-01"
    assert contexto.event.transaction_type == "Pix"
    assert contexto.event.transaction_value == 5000.0
    assert contexto.event.transaction_timestamp == datetime(
        2026,
        8,
        18,
        12,
        0,
        tzinfo=UTC,
    )


def test_build_evidence_context_preserva_resultado_da_deteccao():
    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        alert_id="ALT-EVIDENCE-DETECTION-001",
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

    assert contexto.detection == alerta.detection
    assert contexto.detection.suspicious_probability == 0.90
    assert contexto.detection.anomaly_raw_score == -0.42
    assert contexto.detection.detector == "isolation_forest"


def test_build_evidence_context_preserva_avaliacao_de_risco():
    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        alert_id="ALT-EVIDENCE-RISK-001",
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

    assert contexto.risk == alerta.risk
    assert contexto.risk.score == 92.0
    assert contexto.risk.severity == alerta.risk.severity


def test_build_evidence_context_preserva_timestamp_de_criacao_do_alerta():
    created_at = datetime(
        2026,
        8,
        18,
        13,
        0,
        tzinfo=UTC,
    )

    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        alert_id="ALT-EVIDENCE-TIME-001",
        created_at=created_at,
    )

    contexto = build_evidence_context(alerta)

    assert contexto.alert_created_at == alerta.created_at
    assert contexto.alert_created_at == created_at
