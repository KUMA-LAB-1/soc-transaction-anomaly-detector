import requests

from src.genai.contracts import LlmRequest
from src.genai.providers.gemini import GeminiLlmAdapter


class FakeResponse:
    def __init__(self, *, status_code, payload):
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            response = requests.Response()
            response.status_code = self.status_code

            error = requests.HTTPError(
                f"{self.status_code} error",
                response=response,
            )

            raise error

    def json(self):
        return self._payload


class FakeSession:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []

    def post(self, *args, **kwargs):
        self.calls.append((args, kwargs))
        return self.responses.pop(0)


def test_gemini_respeita_retry_delay_informado_pelo_provider():
    session = FakeSession(
        [
            FakeResponse(
                status_code=429,
                payload={
                    "error": {
                        "details": [
                            {
                                "@type": ("type.googleapis.com/google.rpc.RetryInfo"),
                                "retryDelay": "45s",
                            }
                        ]
                    }
                },
            ),
            FakeResponse(
                status_code=200,
                payload={
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {
                                        "text": "Resposta final.",
                                    }
                                ]
                            }
                        }
                    ]
                },
            ),
        ]
    )

    sleeps = []

    adapter = GeminiLlmAdapter(
        api_key="segredo-de-teste",
        session=session,
        max_attempts=2,
        backoff_base_seconds=1.0,
        sleep_fn=sleeps.append,
    )

    response = adapter.generate(
        LlmRequest(
            system_prompt="system",
            context="context",
            user_message="question",
        )
    )

    assert response.content == "Resposta final."
    assert sleeps == [45.0]
    assert len(session.calls) == 2
