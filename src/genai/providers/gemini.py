from __future__ import annotations

import time
from collections.abc import Callable
from typing import Any

import requests

from ..contracts import LlmRequest, LlmResponse

DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"


class GeminiLlmAdapter:
    """Adapter Gemini isolado atrás do contrato provider-neutral."""

    def __init__(
        self,
        *,
        api_key: str,
        model: str = DEFAULT_GEMINI_MODEL,
        session: Any = None,
        timeout: int = 30,
        max_attempts: int = 3,
        backoff_base_seconds: float = 1.0,
        sleep_fn: Callable[[float], None] = time.sleep,
    ):
        self._api_key = api_key
        self._model = model
        self._session = session or requests
        self._timeout = timeout
        self._max_attempts = max_attempts
        self._backoff_base_seconds = backoff_base_seconds
        self._sleep_fn = sleep_fn

    def generate(self, request: LlmRequest) -> LlmResponse:
        """Traduz LlmRequest para a API Gemini e normaliza a resposta."""

        url = f"{GEMINI_API_BASE_URL}/{self._model}:generateContent"

        payload = {
            "system_instruction": {
                "parts": [
                    {
                        "text": request.system_prompt,
                    }
                ]
            },
            "contents": [
                {
                    "role": "user",
                    "parts": [
                        {
                            "text": (
                                "Contexto estruturado:\n"
                                f"{request.context}"
                                "\n\nPergunta do analista:\n"
                                f"{request.user_message}"
                            )
                        }
                    ],
                }
            ],
        }

        response = None

        for attempt in range(1, self._max_attempts + 1):
            response = self._session.post(
                url,
                headers={
                    "Content-Type": "application/json",
                    "x-goog-api-key": self._api_key,
                },
                json=payload,
                timeout=self._timeout,
            )

            try:
                response.raise_for_status()
                break
            except requests.HTTPError:
                status_code = getattr(
                    response,
                    "status_code",
                    None,
                )
                retryable = (
                    status_code == 429
                    or (
                        status_code is not None
                        and 500 <= status_code < 600
                    )
                )

                if (
                    not retryable
                    or attempt >= self._max_attempts
                ):
                    raise

                delay = self._backoff_base_seconds * (
                    2 ** (attempt - 1)
                )
                self._sleep_fn(delay)

        data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]

        return LlmResponse(
            content=content,
        )
