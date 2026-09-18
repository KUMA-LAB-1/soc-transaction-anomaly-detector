from __future__ import annotations

from dataclasses import dataclass

from ..evidence_context import EvidenceContext


@dataclass
class GuardedSocAssessment:
    alert_id: str
    missing_evidence: tuple[str, ...]


def build_guarded_assessment(context: EvidenceContext) -> GuardedSocAssessment:
    return GuardedSocAssessment(
        alert_id=context.alert_id,
        missing_evidence=context.quality.missing_evidence,
    )
