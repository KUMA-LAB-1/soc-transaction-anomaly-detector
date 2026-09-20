import json

import pytest
import requests

from src.genai.contracts import LlmRequest, LlmResponse
from src.genai.providers.gemini import GeminiLlmAdapter


class FakeResponse:
    def __init__(self, payload, *, status_code=200):
        self.payload = payload
        self.status_code = status_code
        self.raise_for_status_called = False

    def raise_for_status(self):
        self.raise_for_status_called = True

        if self.status_code >= 400:
            raise requests.HTTPError(
                f"HTTP {self.status_code}",
                response=self,
            )

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


class SequenceSession:
    def __init__(self, responses):
        self.responses = list(responses)
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

        return self.responses.pop(0)


def test_gemini_adapter_retry_em_503_e_recupera():
    responses = [
        FakeResponse({}, status_code=503),
        FakeResponse({}, status_code=503),
        FakeResponse(
            {
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {
                                    "text": "Resposta após retry.",
                                }
                            ]
                        }
                    }
                ]
            }
        ),
    ]
    session = SequenceSession(responses)
    sleeps = []

    adapter = GeminiLlmAdapter(
        api_key="test-key",
        session=session,
        max_attempts=3,
        backoff_base_seconds=1.0,
        sleep_fn=sleeps.append,
    )

    result = adapter.generate(build_request())

    assert result == LlmResponse(
        content="Resposta após retry.",
    )
    assert len(session.calls) == 3
    assert sleeps == [1.0, 2.0]


def test_gemini_adapter_nao_retry_em_erro_nao_transitorio():
    response = FakeResponse(
        {},
        status_code=403,
    )
    session = SequenceSession([response])
    sleeps = []

    adapter = GeminiLlmAdapter(
        api_key="test-key",
        session=session,
        max_attempts=3,
        backoff_base_seconds=1.0,
        sleep_fn=sleeps.append,
    )

    with pytest.raises(requests.HTTPError):
        adapter.generate(build_request())

    assert len(session.calls) == 1
    assert sleeps == []


def test_gemini_adapter_esgota_retry_e_propaga_503():
    responses = [
        FakeResponse({}, status_code=503),
        FakeResponse({}, status_code=503),
        FakeResponse({}, status_code=503),
    ]
    session = SequenceSession(responses)
    sleeps = []

    adapter = GeminiLlmAdapter(
        api_key="test-key",
        session=session,
        max_attempts=3,
        backoff_base_seconds=1.0,
        sleep_fn=sleeps.append,
    )

    with pytest.raises(requests.HTTPError):
        adapter.generate(build_request())

    assert len(session.calls) == 3
    assert sleeps == [1.0, 2.0]
