from __future__ import annotations

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
    ):
        self._api_key = api_key
        self._model = model
        self._session = session or requests
        self._timeout = timeout

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

        response = self._session.post(
            url,
            headers={
                "Content-Type": "application/json",
                "x-goog-api-key": self._api_key,
            },
            json=payload,
            timeout=self._timeout,
        )

        response.raise_for_status()

        data = response.json()

        content = data["candidates"][0]["content"]["parts"][0]["text"]

        return LlmResponse(
            content=content,
        )
