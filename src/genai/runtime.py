from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .providers.gemini import DEFAULT_GEMINI_MODEL


class GenAiConfigurationError(ValueError):
    """Erro de configuração da camada GenAI."""


@dataclass(frozen=True)
class GenAiRuntimeConfig:
    gemini_api_key: str = field(repr=False)
    gemini_model: str = DEFAULT_GEMINI_MODEL


def load_genai_runtime_config(
    environment: Mapping[str, str],
) -> GenAiRuntimeConfig:
    """Carrega e valida a configuração necessária para o runtime GenAI."""

    api_key = environment.get("GEMINI_API_KEY", "").strip()

    if not api_key:
        raise GenAiConfigurationError(
            "GEMINI_API_KEY é obrigatória para o runtime GenAI."
        )

    model = environment.get(
        "GEMINI_MODEL",
        DEFAULT_GEMINI_MODEL,
    ).strip()

    if not model:
        model = DEFAULT_GEMINI_MODEL

    return GenAiRuntimeConfig(
        gemini_api_key=api_key,
        gemini_model=model,
    )
