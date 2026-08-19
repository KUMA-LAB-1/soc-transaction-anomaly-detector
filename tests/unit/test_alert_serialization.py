import json
from datetime import UTC, datetime

import pytest

from src.alerts.contract import (
    ALERT_SCHEMA_VERSION,
    Alert,
    AlertDetection,
    AlertEvent,
    AlertEvidence,
    AlertMitre,
    AlertQuality,
    AlertRisk,
    EvidenceValue,
)
from src.alerts.serialization import (
    alert_from_dict,
    alert_from_json,
    alert_to_dict,
    alert_to_json,
)


def test_alert_to_dict_preserva_schema_version():
    dados = alert_to_dict(criar_alerta_serializacao())

    assert dados["schema_version"] == ALERT_SCHEMA_VERSION


def criar_alerta_serializacao() -> Alert:
    return Alert(
        alert_id="ALT-001",
        created_at=datetime(
            2026,
            8,
            18,
            15,
            30,
            tzinfo=UTC,
        ),
        event=AlertEvent(
            transaction_id=101,
            customer_pseudonym="cliente-ç-01",
            transaction_type="Pix",
            transaction_value=5000.0,
            transaction_timestamp=datetime(
                2026,
                8,
                18,
                15,
                0,
                tzinfo=UTC,
            ),
        ),
        detection=AlertDetection(
            suspicious_probability=0.91,
            anomaly_detected=True,
            anomaly_raw_score=-0.42,
            detector="isolation_forest",
        ),
        risk=AlertRisk(
            score=92.0,
            severity="critical",
        ),
        evidence=AlertEvidence(
            failed_logins=EvidenceValue(
                value=4,
                observed=True,
            ),
            new_device=EvidenceValue(
                value=True,
                observed=True,
            ),
            limit_change=EvidenceValue(
                value=False,
                observed=False,
            ),
            location_change=EvidenceValue(
                value=False,
                observed=True,
            ),
        ),
        mitre=AlertMitre(),
        quality=AlertQuality(
            small_sample_warning=True,
            missing_evidence=("alteracao_limite_flag",),
        ),
    )


def test_alert_to_dict_preserva_estrutura_aninhada():
    dados = alert_to_dict(criar_alerta_serializacao())

    assert dados["alert_id"] == "ALT-001"
    assert dados["event"]["transaction_id"] == 101
    assert dados["detection"]["anomaly_detected"] is True
    assert dados["risk"]["severity"] == "critical"
    assert dados["evidence"]["failed_logins"]["value"] == 4


def test_alert_to_dict_serializa_datetimes_com_iso_8601():
    dados = alert_to_dict(criar_alerta_serializacao())

    assert dados["created_at"] == "2026-08-18T15:30:00+00:00"
    assert dados["event"]["transaction_timestamp"] == "2026-08-18T15:00:00+00:00"


def test_alert_to_dict_converte_tuple_em_lista():
    dados = alert_to_dict(criar_alerta_serializacao())

    assert dados["quality"]["missing_evidence"] == [
        "alteracao_limite_flag",
    ]


def test_alert_to_dict_preserva_none():
    dados = alert_to_dict(criar_alerta_serializacao())

    assert dados["mitre"]["technique_id"] is None
    assert dados["mitre"]["technique"] is None
    assert dados["mitre"]["tactic"] is None


def test_alert_to_json_produz_json_valido():
    conteudo = alert_to_json(criar_alerta_serializacao())

    dados = json.loads(conteudo)

    assert dados["alert_id"] == "ALT-001"
    assert dados["risk"]["score"] == 92.0


def test_alert_to_json_preserva_unicode():
    conteudo = alert_to_json(criar_alerta_serializacao())

    assert "cliente-ç-01" in conteudo
    assert "\\u00e7" not in conteudo


def test_alert_to_json_aceita_indentacao():
    conteudo = alert_to_json(
        criar_alerta_serializacao(),
        indent=2,
    )

    assert "\n" in conteudo
    assert '  "alert_id": "ALT-001"' in conteudo


def test_alert_to_json_preserva_contrato_ao_recarregar():
    alerta = criar_alerta_serializacao()

    conteudo = alert_to_json(alerta)
    dados = json.loads(conteudo)

    assert dados["schema_version"] == alerta.schema_version
    assert dados["alert_id"] == alerta.alert_id

    assert dados["event"]["transaction_id"] == alerta.event.transaction_id
    assert dados["event"]["customer_pseudonym"] == alerta.event.customer_pseudonym

    assert (
        dados["detection"]["suspicious_probability"]
        == alerta.detection.suspicious_probability
    )
    assert dados["detection"]["anomaly_detected"] is alerta.detection.anomaly_detected

    assert dados["risk"]["score"] == alerta.risk.score
    assert dados["risk"]["severity"] == alerta.risk.severity

    assert (
        dados["evidence"]["failed_logins"]["value"]
        == alerta.evidence.failed_logins.value
    )
    assert (
        dados["evidence"]["failed_logins"]["observed"]
        is alerta.evidence.failed_logins.observed
    )


def test_alert_from_dict_reconstroi_alert():
    original = criar_alerta_serializacao()

    reconstruido = alert_from_dict(alert_to_dict(original))

    assert reconstruido == original


def test_alert_from_json_reconstroi_alert():
    original = criar_alerta_serializacao()

    reconstruido = alert_from_json(alert_to_json(original))

    assert reconstruido == original


def test_alert_from_dict_reconstroi_datetime():
    original = criar_alerta_serializacao()

    reconstruido = alert_from_dict(alert_to_dict(original))

    assert isinstance(reconstruido.created_at, datetime)
    assert isinstance(
        reconstruido.event.transaction_timestamp,
        datetime,
    )


def test_alert_from_dict_reconstroi_missing_evidence_como_tuple():
    original = criar_alerta_serializacao()

    reconstruido = alert_from_dict(alert_to_dict(original))

    assert isinstance(
        reconstruido.quality.missing_evidence,
        tuple,
    )


def test_alert_from_dict_preserva_none():
    original = criar_alerta_serializacao()

    dados = alert_to_dict(original)
    dados["mitre"]["technique_id"] = None

    reconstruido = alert_from_dict(dados)

    assert reconstruido.mitre.technique_id is None


def test_alert_from_dict_rejeita_schema_version_desconhecida():
    original = criar_alerta_serializacao()

    dados = alert_to_dict(original)
    dados["schema_version"] = "999.0"

    with pytest.raises(
        ValueError,
        match="versão de schema de alerta não suportada",
    ):
        alert_from_dict(dados)


def test_alert_from_json_rejeita_estrutura_que_nao_seja_objeto():
    with pytest.raises(
        ValueError,
        match="JSON do alerta deve representar um objeto",
    ):
        alert_from_json("[]")


def test_alert_from_json_rejeita_json_invalido():
    with pytest.raises(json.JSONDecodeError):
        alert_from_json("{json-invalido")


def test_alert_from_dict_preserva_timezone():
    original = criar_alerta_serializacao()

    reconstruido = alert_from_dict(alert_to_dict(original))

    assert reconstruido.created_at.tzinfo is not None
    assert reconstruido.event.transaction_timestamp.tzinfo is not None
