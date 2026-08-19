from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .contract import (
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


def _normalizar_valor(valor: Any) -> Any:
    """Converte valores do domínio para tipos compatíveis com JSON."""
    if isinstance(valor, datetime):
        return valor.isoformat()

    if isinstance(valor, tuple):
        return [_normalizar_valor(item) for item in valor]

    if isinstance(valor, list):
        return [_normalizar_valor(item) for item in valor]

    if isinstance(valor, dict):
        return {chave: _normalizar_valor(item) for chave, item in valor.items()}

    return valor


def _evidence_value_from_dict(dados: dict[str, Any]) -> EvidenceValue:
    """Reconstrói uma evidência individual a partir de dados serializados."""
    return EvidenceValue(
        value=dados["value"],
        observed=dados.get("observed", True),
    )


def alert_to_dict(alert: Alert) -> dict[str, Any]:
    """Serializa um Alert para uma estrutura Python compatível com JSON."""
    dados = asdict(alert)
    return _normalizar_valor(dados)


def alert_to_json(
    alert: Alert,
    *,
    indent: int | None = None,
) -> str:
    """Serializa um Alert para JSON UTF-8 preservando caracteres Unicode."""
    return json.dumps(
        alert_to_dict(alert),
        ensure_ascii=False,
        indent=indent,
    )


def alert_from_dict(dados: dict[str, Any]) -> Alert:
    """Reconstrói um Alert a partir de uma estrutura Python serializada."""
    schema_version = dados.get("schema_version", ALERT_SCHEMA_VERSION)

    if schema_version != ALERT_SCHEMA_VERSION:
        raise ValueError(
            f"versão de schema de alerta não suportada: {schema_version!r}"
        )

    evento = dados["event"]
    detection = dados["detection"]
    risk = dados["risk"]
    evidence = dados["evidence"]
    mitre = dados.get("mitre", {})
    quality = dados.get("quality", {})

    return Alert(
        alert_id=dados["alert_id"],
        created_at=datetime.fromisoformat(dados["created_at"]),
        event=AlertEvent(
            transaction_id=evento.get("transaction_id"),
            customer_pseudonym=evento["customer_pseudonym"],
            transaction_type=evento["transaction_type"],
            transaction_value=float(evento["transaction_value"]),
            transaction_timestamp=datetime.fromisoformat(
                evento["transaction_timestamp"]
            ),
        ),
        detection=AlertDetection(
            suspicious_probability=float(detection["suspicious_probability"]),
            anomaly_detected=bool(detection["anomaly_detected"]),
            anomaly_raw_score=float(detection["anomaly_raw_score"]),
            detector=detection["detector"],
        ),
        risk=AlertRisk(
            score=float(risk["score"]),
            severity=risk["severity"],
        ),
        evidence=AlertEvidence(
            failed_logins=_evidence_value_from_dict(evidence["failed_logins"]),
            new_device=_evidence_value_from_dict(evidence["new_device"]),
            limit_change=_evidence_value_from_dict(evidence["limit_change"]),
            location_change=_evidence_value_from_dict(evidence["location_change"]),
        ),
        mitre=AlertMitre(
            technique_id=mitre.get("technique_id"),
            technique=mitre.get("technique"),
            tactic=mitre.get("tactic"),
            criterion=mitre.get("criterion"),
            source=mitre.get("source"),
            procedures=mitre.get("procedures"),
        ),
        quality=AlertQuality(
            small_sample_warning=quality.get(
                "small_sample_warning",
                False,
            ),
            missing_evidence=tuple(
                quality.get(
                    "missing_evidence",
                    [],
                )
            ),
        ),
        schema_version=schema_version,
    )


def alert_from_json(conteudo: str) -> Alert:
    """Reconstrói um Alert a partir de uma representação JSON."""
    dados = json.loads(conteudo)

    if not isinstance(dados, dict):
        raise ValueError("o JSON do alerta deve representar um objeto")

    return alert_from_dict(dados)
