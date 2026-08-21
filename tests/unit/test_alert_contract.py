from dataclasses import FrozenInstanceError
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


def criar_alerta() -> Alert:
    return Alert(
        alert_id="ALT-001",
        created_at=datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
        event=AlertEvent(
            transaction_id=101,
            customer_pseudonym="cliente-001",
            transaction_type="Pix",
            transaction_value=5000.0,
            transaction_timestamp=datetime(2026, 8, 18, 11, 30, tzinfo=UTC),
        ),
        detection=AlertDetection(
            suspicious_probability=0.94,
            anomaly_detected=True,
            anomaly_raw_score=-0.42,
            detector="isolation_forest",
        ),
        risk=AlertRisk(
            score=91.5,
            severity="critical",
        ),
        evidence=AlertEvidence(
            failed_logins=EvidenceValue(value=4, observed=True),
            new_device=EvidenceValue(value=True, observed=True),
            limit_change=EvidenceValue(value=True, observed=True),
            location_change=EvidenceValue(value=False, observed=True),
        ),
        mitre=AlertMitre(
            technique_id="T1110",
            technique="Brute Force",
            tactic="Credential Access",
            criterion="multiple failed logins",
            source="test",
            procedures="Review authentication events.",
        ),
        quality=AlertQuality(
            small_sample_warning=False,
            missing_evidence=(),
        ),
    )


def test_alert_contract_armazena_dados_estruturados():
    alerta = criar_alerta()

    assert alerta.alert_id == "ALT-001"
    assert alerta.event.transaction_id == 101
    assert alerta.detection.anomaly_detected is True
    assert alerta.risk.score == 91.5
    assert alerta.evidence.failed_logins.value == 4
    assert alerta.mitre.technique_id == "T1110"


def test_alert_contract_usa_schema_version_padrao():
    alerta = criar_alerta()

    assert alerta.schema_version == ALERT_SCHEMA_VERSION


def test_evidence_value_distingue_ausencia_de_dado():
    evidencia = EvidenceValue(
        value=False,
        observed=False,
    )

    assert evidencia.value is False
    assert evidencia.observed is False


def test_alert_contract_permite_transaction_id_ausente():
    alerta = criar_alerta()

    evento_sem_id = AlertEvent(
        transaction_id=None,
        customer_pseudonym=alerta.event.customer_pseudonym,
        transaction_type=alerta.event.transaction_type,
        transaction_value=alerta.event.transaction_value,
        transaction_timestamp=alerta.event.transaction_timestamp,
    )

    assert evento_sem_id.transaction_id is None


def test_alert_contract_e_imutavel():
    alerta = criar_alerta()

    with pytest.raises(FrozenInstanceError):
        alerta.alert_id = "OUTRO"
