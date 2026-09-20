import json

from src.genai.contracts import LlmRequest, LlmResponse
from src.genai.providers.gemini import GeminiLlmAdapter


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
        context=('{"alert_id":"ALT-GEMINI-001","incident_confirmed":false}'),
        user_message="Este incidente está confirmado?",
    )


def test_gemini_adapter_traduz_request_para_api():
    response = FakeResponse(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [{"text": ("O contexto não confirma um incidente.")}]
                    }
                }
            ]
        }
    )
    session = RecordingSession(response)

    adapter = GeminiLlmAdapter(
        api_key="test-api-key",
        model="gemini-3.8-flash",
        session=session,
    )

    result = adapter.generate(build_request())

    assert result == LlmResponse(
        content="O contexto não confirma um incidente.",
    )
    assert response.raise_for_status_called is True
    assert len(session.calls) == 1

    call = session.calls[0]

    assert call["url"] == (
        "https://generativelanguage.googleapis.com/"
        "v1beta/models/gemini-3.8-flash:generateContent"
    )
    assert call["headers"] == {
        "Content-Type": "application/json",
        "x-goog-api-key": "test-api-key",
    }
    assert call["timeout"] == 30

    assert call["json"]["system_instruction"] == {
        "parts": [
            {
                "text": "Use somente o contexto fornecido.",
            }
        ]
    }

    assert call["json"]["contents"] == [
        {
            "role": "user",
            "parts": [
                {
                    "text": (
                        "Contexto estruturado:\n"
                        '{"alert_id":"ALT-GEMINI-001",'
                        '"incident_confirmed":false}'
                        "\n\nPergunta do analista:\n"
                        "Este incidente está confirmado?"
                    )
                }
            ],
        }
    ]


def test_gemini_adapter_nao_expoe_api_key_no_payload():
    response = FakeResponse(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Resposta segura.",
                            }
                        ]
                    }
                }
            ]
        }
    )
    session = RecordingSession(response)

    adapter = GeminiLlmAdapter(
        api_key="secret-test-key",
        session=session,
    )

    adapter.generate(build_request())

    payload = session.calls[0]["json"]

    assert "secret-test-key" not in json.dumps(payload)


def test_gemini_adapter_usa_modelo_padrao_estavel():
    response = FakeResponse(
        {
            "candidates": [
                {
                    "content": {
                        "parts": [
                            {
                                "text": "Resposta.",
                            }
                        ]
                    }
                }
            ]
        }
    )
    session = RecordingSession(response)

    adapter = GeminiLlmAdapter(
        api_key="test-key",
        session=session,
    )

    adapter.generate(build_request())

    assert session.calls[0]["url"].endswith("/models/gemini-3.8-flash:generateContent")
