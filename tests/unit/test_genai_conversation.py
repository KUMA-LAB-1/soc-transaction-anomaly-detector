import copy
import json

from src.genai.contracts import LlmRequest, LlmResponse
from src.genai.conversation import ConversationService
from src.soc_assistant.assessment import (
    GuardedSocAssessment,
    ObservedFact,
    RecommendedCheck,
    SupportedHypothesis,
)


class RecordingLlmAdapter:
    def __init__(self, response: LlmResponse):
        self.response = response
        self.requests: list[LlmRequest] = []

    def generate(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return self.response


def build_assessment() -> GuardedSocAssessment:
    return GuardedSocAssessment(
        alert_id="ALT-CONV-001",
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


def test_conversation_service_orquestra_request_e_adapter():
    assessment = build_assessment()

    expected_response = LlmResponse(
        content="O incidente ainda não está confirmado.",
    )

    adapter = RecordingLlmAdapter(expected_response)
    service = ConversationService(adapter)

    response = service.ask(
        assessment,
        user_message="Este incidente está confirmado?",
    )

    assert response == expected_response
    assert len(adapter.requests) == 1

    request = adapter.requests[0]
    context = json.loads(request.context)

    assert request.user_message == "Este incidente está confirmado?"
    assert context["alert_id"] == "ALT-CONV-001"
    assert context["incident_confirmed"] is False


def test_conversation_service_preserva_assessment_original():
    assessment = build_assessment()
    original = copy.deepcopy(assessment)

    adapter = RecordingLlmAdapter(
        LlmResponse(
            content="Investigue a evidência ausente.",
        )
    )
    service = ConversationService(adapter)

    service.ask(
        assessment,
        user_message="O que devo investigar agora?",
    )

    assert assessment == original


def test_conversation_service_envia_contexto_defensivo_ao_adapter():
    assessment = build_assessment()

    adapter = RecordingLlmAdapter(
        LlmResponse(
            content="Resposta baseada no contexto.",
        )
    )
    service = ConversationService(adapter)

    service.ask(
        assessment,
        user_message="Resuma o alerta.",
    )

    request = adapter.requests[0]
    context = json.loads(request.context)

    assert context["facts"] == [
        {
            "name": "failed_logins",
            "value": 5,
        },
        {
            "name": "new_device",
            "value": True,
        },
    ]
    assert context["missing_evidence"] == ["location_change"]
    assert context["hypotheses"] == [
        {
            "statement": "possible_account_compromise",
            "supporting_fact_names": [
                "failed_logins",
                "new_device",
            ],
        }
    ]
