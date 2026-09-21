import pytest
import requests

from src.genai.contracts import LlmRequest
from src.genai.providers.gemini import GeminiLlmAdapter


class FakeResponse:
    status_code = 200

    def raise_for_status(self):
        return None

    def json(self):
        return {
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
        }


class ScriptedSession:
    def __init__(self, actions):
        self.actions = list(actions)
        self.call_count = 0

    def post(self, *args, **kwargs):
        self.call_count += 1

        action = self.actions.pop(0)

        if isinstance(action, BaseException):
            raise action

        return action


def _request():
    return LlmRequest(
        system_prompt="system",
        context="context",
        user_message="question",
    )


def test_gemini_retrya_read_timeout_e_recupera():
    session = ScriptedSession(
        [
            requests.ReadTimeout(
                "read timeout",
            ),
            FakeResponse(),
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
        _request(),
    )

    assert response.content == "Resposta final."
    assert session.call_count == 2
    assert sleeps == [1.0]


def test_gemini_propaga_read_timeout_apos_esgotar_retries():
    session = ScriptedSession(
        [
            requests.ReadTimeout(
                "timeout-1",
            ),
            requests.ReadTimeout(
                "timeout-2",
            ),
            requests.ReadTimeout(
                "timeout-3",
            ),
        ]
    )

    sleeps = []

    adapter = GeminiLlmAdapter(
        api_key="segredo-de-teste",
        session=session,
        max_attempts=3,
        backoff_base_seconds=1.0,
        sleep_fn=sleeps.append,
    )

    with pytest.raises(
        requests.ReadTimeout,
    ):
        adapter.generate(
            _request(),
        )

    assert session.call_count == 3
    assert sleeps == [
        1.0,
        2.0,
    ]
