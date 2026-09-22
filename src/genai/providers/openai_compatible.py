from __future__ import annotations

from typing import Any

import requests

from ..contracts import LlmRequest, LlmResponse


class OpenAiCompatibleLlmAdapter:
    """Adapter para providers com endpoint OpenAI-compatible."""

    def __init__(
        self,
        *,
        base_url: str,
        model: str,
        api_key: str | None = None,
        session: Any = None,
        timeout: int = 30,
    ):
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._session = session or requests
        self._timeout = timeout

    def generate(
        self,
        request: LlmRequest,
    ) -> LlmResponse:
        """Traduz LlmRequest para Chat Completions e normaliza a resposta."""

        url = f"{self._base_url}/chat/completions"

        headers = {
            "Content-Type": "application/json",
        }

        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"

        payload = {
            "model": self._model,
            "messages": [
                {
                    "role": "system",
                    "content": request.system_prompt,
                },
                {
                    "role": "user",
                    "content": (
                        "Contexto estruturado:\n"
                        f"{request.context}"
                        "\n\nPergunta do analista:\n"
                        f"{request.user_message}"
                    ),
                },
            ],
            "stream": False,
        }

        response = self._session.post(
            url,
            headers=headers,
            json=payload,
            timeout=self._timeout,
        )

        response.raise_for_status()

        data = response.json()

        content = data["choices"][0]["message"]["content"]

        return LlmResponse(
            content=content,
        )
