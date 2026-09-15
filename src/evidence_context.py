from __future__ import annotations

from dataclasses import dataclass

from .alerts.contract import Alert, AlertEvidence, AlertQuality


@dataclass(frozen=True)
class EvidenceContext:
    evidence: AlertEvidence
    quality: AlertQuality


def build_evidence_context(alert: Alert) -> EvidenceContext:
    """Projeta um Alert em um contexto de evidência sem reinterpretar seus dados."""
    return EvidenceContext(
        evidence=alert.evidence,
        quality=alert.quality,
    )
