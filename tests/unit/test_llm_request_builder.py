import json

from src.genai.request_builder import (
    PUBLIC_SYSTEM_PROMPT,
    build_llm_request,
)
from src.soc_assistant.assessment import (
    GuardedSocAssessment,
    ObservedFact,
    RecommendedCheck,
    SupportedHypothesis,
)


def build_assessment() -> GuardedSocAssessment:
    return GuardedSocAssessment(
        alert_id="ALT-GENAI-001",
        missing_evidence=(
            "limit_change",
            "location_change",
        ),
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
                evidence_name="limit_change",
            ),
            RecommendedCheck(
                action="collect_missing_evidence",
                evidence_name="location_change",
            ),
        ),
        incident_confirmed=False,
    )


def test_request_builder_projeta_assessment_em_contexto_estruturado():
    assessment = build_assessment()

    request = build_llm_request(
        assessment,
        user_message="Este incidente está confirmado?",
    )

    context = json.loads(request.context)

    assert context == {
        "alert_id": "ALT-GENAI-001",
        "facts": [
            {
                "name": "failed_logins",
                "value": 5,
            },
            {
                "name": "new_device",
                "value": True,
            },
        ],
        "hypotheses": [
            {
                "statement": "possible_account_compromise",
                "supporting_fact_names": [
                    "failed_logins",
                    "new_device",
                ],
            },
        ],
        "incident_confirmed": False,
        "missing_evidence": [
            "limit_change",
            "location_change",
        ],
        "recommended_checks": [
            {
                "action": "collect_missing_evidence",
                "evidence_name": "limit_change",
            },
            {
                "action": "collect_missing_evidence",
                "evidence_name": "location_change",
            },
        ],
    }


def test_request_builder_preserva_pergunta_e_prompt_publico():
    assessment = build_assessment()

    request = build_llm_request(
        assessment,
        user_message="O que devo investigar agora?",
    )

    assert request.system_prompt == PUBLIC_SYSTEM_PROMPT
    assert request.user_message == "O que devo investigar agora?"


def test_prompt_publico_preserva_limite_de_confirmacao():
    assert "contexto" in PUBLIC_SYSTEM_PROMPT.lower()
    assert "incidente" in PUBLIC_SYSTEM_PROMPT.lower()
    assert "confirm" in PUBLIC_SYSTEM_PROMPT.lower()
