from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

from .alerts.contract import (
    Alert,
    AlertDetection,
    AlertEvent,
    AlertEvidence,
    AlertQuality,
    AlertRisk,
)


@dataclass(frozen=True)
class EvidenceContext:
    alert_id: str
    alert_created_at: datetime
    source_schema_version: str
    event: AlertEvent
    detection: AlertDetection
    risk: AlertRisk
    evidence: AlertEvidence
    quality: AlertQuality


def build_evidence_context(alert: Alert) -> EvidenceContext:
    """Projeta um Alert em um contexto de evidência sem reinterpretar seus dados."""
    return EvidenceContext(
        alert_id=alert.alert_id,
        alert_created_at=alert.created_at,
        source_schema_version=alert.schema_version,
        event=alert.event,
        detection=alert.detection,
        risk=alert.risk,
        evidence=alert.evidence,
        quality=alert.quality,
    )
