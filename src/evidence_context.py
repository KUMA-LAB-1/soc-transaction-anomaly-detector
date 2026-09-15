from __future__ import annotations

from dataclasses import dataclass

from .alerts.contract import Alert, AlertEvidence, AlertQuality


@dataclass(frozen=True)
class EvidenceContext:
    alert_id: str
    source_schema_version: str
    evidence: AlertEvidence
    quality: AlertQuality


def build_evidence_context(alert: Alert) -> EvidenceContext:
    """Projeta um Alert em um contexto de evidência sem reinterpretar seus dados."""
    return EvidenceContext(
        alert_id=alert.alert_id,
        source_schema_version=alert.schema_version,
        evidence=alert.evidence,
        quality=alert.quality,
    )
