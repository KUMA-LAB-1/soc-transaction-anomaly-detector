from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..evidence_context import EvidenceContext


@dataclass
class ObservedFact:
    name: str
    value: Any


@dataclass
class SupportedHypothesis:
    statement: str
    supporting_fact_names: tuple[str, ...]


@dataclass
class RecommendedCheck:
    action: str
    evidence_name: str


@dataclass
class GuardedSocAssessment:
    alert_id: str
    missing_evidence: tuple[str, ...]
    facts: tuple[ObservedFact, ...]
    hypotheses: tuple[SupportedHypothesis, ...]
    recommended_checks: tuple[RecommendedCheck, ...]
    incident_confirmed: bool


def build_guarded_assessment(context: EvidenceContext) -> GuardedSocAssessment:
    facts = tuple(
        ObservedFact(
            name=name,
            value=evidence.value,
        )
        for name, evidence in (
            ("failed_logins", context.evidence.failed_logins),
            ("new_device", context.evidence.new_device),
            ("limit_change", context.evidence.limit_change),
            ("location_change", context.evidence.location_change),
        )
        if evidence.observed
    )

    recommended_checks = tuple(
        RecommendedCheck(
            action="collect_missing_evidence",
            evidence_name=evidence_name,
        )
        for evidence_name in context.quality.missing_evidence
    )

    return GuardedSocAssessment(
        alert_id=context.alert_id,
        missing_evidence=context.quality.missing_evidence,
        facts=facts,
        hypotheses=(),
        recommended_checks=recommended_checks,
        incident_confirmed=False,
    )


def add_supported_hypothesis(
    assessment: GuardedSocAssessment,
    *,
    statement: str,
    supporting_fact_names: tuple[str, ...],
) -> GuardedSocAssessment:
    if not supporting_fact_names:
        raise ValueError("supporting facts must not be empty")

    observed_fact_names = {fact.name for fact in assessment.facts}

    if not set(supporting_fact_names).issubset(observed_fact_names):
        raise ValueError("supporting facts must be observed")

    assessment.hypotheses += (
        SupportedHypothesis(
            statement=statement,
            supporting_fact_names=supporting_fact_names,
        ),
    )
    return assessment
