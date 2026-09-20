from __future__ import annotations

from src.soc_assistant.assessment import GuardedSocAssessment

from .contracts import LlmAdapter, LlmResponse
from .request_builder import build_llm_request


class ConversationService:
    """Orquestra a conversa entre assessment defensivo e adapter LLM."""

    def __init__(self, adapter: LlmAdapter):
        self._adapter = adapter

    def ask(
        self,
        assessment: GuardedSocAssessment,
        *,
        user_message: str,
    ) -> LlmResponse:
        """Constrói a requisição defensiva e delega a geração ao adapter."""

        request = build_llm_request(
            assessment,
            user_message=user_message,
        )

        return self._adapter.generate(request)
