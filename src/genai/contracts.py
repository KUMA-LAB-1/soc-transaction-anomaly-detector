from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class LlmRequest:
    system_prompt: str
    context: str
    user_message: str


@dataclass(frozen=True)
class LlmResponse:
    content: str


@runtime_checkable
class LlmAdapter(Protocol):
    """Contrato mínimo provider-neutral para geração de resposta."""

    def generate(self, request: LlmRequest) -> LlmResponse:
        """Gera uma resposta a partir de uma requisição já preparada."""
        ...
