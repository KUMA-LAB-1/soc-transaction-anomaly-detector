from __future__ import annotations

from src.soc_assistant.assessment import (
    GuardedSocAssessment,
    ObservedFact,
    RecommendedCheck,
    SupportedHypothesis,
)


def build_demo_assessment() -> GuardedSocAssessment:
    """Constrói o cenário sintético canônico da demo GenAI."""

    return GuardedSocAssessment(
        alert_id="ALT-DEMO-001",
        missing_evidence=("location_change",),
        facts=(
            ObservedFact(
                name="failed_logins",
                value=5,
            ),
            ObservedFact(
                name="new_device",
                value=True,
            ),
        ),
        hypotheses=(
            SupportedHypothesis(
                statement="possible_account_compromise",
                supporting_fact_names=(
                    "failed_logins",
                    "new_device",
                ),
            ),
        ),
        recommended_checks=(
            RecommendedCheck(
                action="collect_missing_evidence",
                evidence_name="location_change",
            ),
        ),
        incident_confirmed=False,
    )
