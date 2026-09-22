from src.genai.contracts import LlmRequest, LlmResponse
from src.genai.providers.openai_compatible import (
    OpenAiCompatibleLlmAdapter,
)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload
        self.raise_for_status_called = False

    def raise_for_status(self):
        self.raise_for_status_called = True

    def json(self):
        return self.payload


class RecordingSession:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def post(
        self,
        url,
        *,
        headers,
        json,
        timeout,
    ):
        self.calls.append(
            {
                "url": url,
                "headers": headers,
                "json": json,
                "timeout": timeout,
            }
        )
        return self.response


def build_request() -> LlmRequest:
    return LlmRequest(
        system_prompt="Use somente o contexto fornecido.",
        context=('{"alert_id":"ALT-LOCAL-001","incident_confirmed":false}'),
        user_message="Este incidente está confirmado?",
    )


def test_openai_compatible_adapter_traduz_request_e_resposta():
    response = FakeResponse(
        {
            "choices": [
                {"message": {"content": ("O contexto não confirma um incidente.")}}
            ]
        }
    )
    session = RecordingSession(response)

    adapter = OpenAiCompatibleLlmAdapter(
        base_url="http://localhost:11434/v1",
        model="qwen3:4b-instruct",
        session=session,
    )

    result = adapter.generate(build_request())

    assert result == LlmResponse(
        content="O contexto não confirma um incidente.",
    )
    assert response.raise_for_status_called is True
    assert len(session.calls) == 1

    call = session.calls[0]

    assert call["url"] == ("http://localhost:11434/v1/chat/completions")
    assert call["headers"] == {
        "Content-Type": "application/json",
    }
    assert call["timeout"] == 30

    assert call["json"] == {
        "model": "qwen3:4b-instruct",
        "messages": [
            {
                "role": "system",
                "content": ("Use somente o contexto fornecido."),
            },
            {
                "role": "user",
                "content": (
                    "Contexto estruturado:\n"
                    '{"alert_id":"ALT-LOCAL-001",'
                    '"incident_confirmed":false}'
                    "\n\nPergunta do analista:\n"
                    "Este incidente está confirmado?"
                ),
            },
        ],
        "stream": False,
    }


def test_openai_compatible_adapter_adiciona_bearer_quando_api_key_existe():
    response = FakeResponse({"choices": [{"message": {"content": "Resposta."}}]})
    session = RecordingSession(response)

    adapter = OpenAiCompatibleLlmAdapter(
        base_url="https://provider.example/v1/",
        model="modelo-teste",
        api_key="secret-test-key",
        session=session,
    )

    adapter.generate(build_request())

    call = session.calls[0]

    assert call["url"] == ("https://provider.example/v1/chat/completions")
    assert call["headers"] == {
        "Content-Type": "application/json",
        "Authorization": "Bearer secret-test-key",
    }


def test_openai_compatible_adapter_nao_expoe_chave_no_payload():
    response = FakeResponse({"choices": [{"message": {"content": "Resposta."}}]})
    session = RecordingSession(response)

    adapter = OpenAiCompatibleLlmAdapter(
        base_url="https://provider.example/v1",
        model="modelo-teste",
        api_key="secret-test-key",
        session=session,
    )

    adapter.generate(build_request())

    payload = session.calls[0]["json"]

    assert "secret-test-key" not in str(payload)
