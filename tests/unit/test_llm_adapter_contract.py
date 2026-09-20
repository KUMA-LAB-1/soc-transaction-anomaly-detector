from src.genai.contracts import (
    LlmAdapter,
    LlmRequest,
    LlmResponse,
)


class FakeLlmAdapter:
    def __init__(self, response: LlmResponse):
        self.response = response
        self.requests: list[LlmRequest] = []

    def generate(self, request: LlmRequest) -> LlmResponse:
        self.requests.append(request)
        return self.response


def test_llm_adapter_aceita_implementacao_provider_neutral():
    request = LlmRequest(
        system_prompt="Use somente o contexto fornecido.",
        context=(
            "alert_id=ALT-LLM-001\n"
            "failed_logins=5\n"
            "new_device=true\n"
            "incident_confirmed=false"
        ),
        user_message="Este incidente está confirmado?",
    )

    expected_response = LlmResponse(
        content="O contexto fornecido não confirma um incidente.",
    )

    adapter = FakeLlmAdapter(expected_response)

    assert isinstance(adapter, LlmAdapter)

    response = adapter.generate(request)

    assert adapter.requests == [request]
    assert response == expected_response


def test_llm_request_preserva_contexto_sem_reinterpretacao():
    request = LlmRequest(
        system_prompt="System prompt acadêmico.",
        context="incident_confirmed=false",
        user_message="Confirme o incidente.",
    )

    assert request.system_prompt == "System prompt acadêmico."
    assert request.context == "incident_confirmed=false"
    assert request.user_message == "Confirme o incidente."
