from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

ALERT_SCHEMA_VERSION = "1.0"


@dataclass(frozen=True)
class EvidenceValue:
    value: Any
    observed: bool = True


@dataclass(frozen=True)
class AlertEvent:
    transaction_id: int | str | None
    customer_pseudonym: str
    transaction_type: str
    transaction_value: float
    transaction_timestamp: datetime


@dataclass(frozen=True)
class AlertDetection:
    suspicious_probability: float
    anomaly_detected: bool
    anomaly_raw_score: float
    detector: str


@dataclass(frozen=True)
class AlertRisk:
    score: float
    severity: str


@dataclass(frozen=True)
class AlertEvidence:
    failed_logins: EvidenceValue
    new_device: EvidenceValue
    limit_change: EvidenceValue
    location_change: EvidenceValue


@dataclass(frozen=True)
class AlertMitre:
    technique_id: str | None = None
    technique: str | None = None
    tactic: str | None = None
    criterion: str | None = None
    source: str | None = None
    procedures: str | None = None


@dataclass(frozen=True)
class AlertQuality:
    small_sample_warning: bool = False
    missing_evidence: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class Alert:
    alert_id: str
    created_at: datetime
    event: AlertEvent
    detection: AlertDetection
    risk: AlertRisk
    evidence: AlertEvidence
    mitre: AlertMitre = field(default_factory=AlertMitre)
    quality: AlertQuality = field(default_factory=AlertQuality)
    schema_version: str = ALERT_SCHEMA_VERSION
