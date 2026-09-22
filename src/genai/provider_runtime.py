from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

from .contracts import LlmAdapter
from .providers.gemini import (
    DEFAULT_GEMINI_MODEL,
    GeminiLlmAdapter,
)
from .providers.openai_compatible import (
    OpenAiCompatibleLlmAdapter,
)

DEFAULT_LLM_PROVIDER = "gemini"
DEFAULT_OLLAMA_MODEL = "qwen3:4b-instruct"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"


class LlmProviderConfigurationError(ValueError):
    """Invalid configuration for the conversational LLM runtime."""


@dataclass(frozen=True)
class LlmProviderRuntimeConfig:
    provider: str
    model: str
    api_key: str | None = field(
        default=None,
        repr=False,
    )
    base_url: str | None = None


def load_llm_provider_runtime_config(
    environment: Mapping[str, str],
) -> LlmProviderRuntimeConfig:
    """Load provider-neutral configuration for conversational GenAI."""

    provider = (
        environment.get(
            "LLM_PROVIDER",
            DEFAULT_LLM_PROVIDER,
        )
        .strip()
        .lower()
    )

    if not provider:
        provider = DEFAULT_LLM_PROVIDER

    if provider == "gemini":
        api_key = environment.get(
            "GEMINI_API_KEY",
            "",
        ).strip()

        if not api_key:
            raise LlmProviderConfigurationError(
                "GEMINI_API_KEY is required when LLM_PROVIDER=gemini."
            )

        model = environment.get(
            "GEMINI_MODEL",
            DEFAULT_GEMINI_MODEL,
        ).strip()

        if not model:
            model = DEFAULT_GEMINI_MODEL

        return LlmProviderRuntimeConfig(
            provider="gemini",
            model=model,
            api_key=api_key,
            base_url=None,
        )

    if provider == "ollama":
        model = environment.get(
            "OLLAMA_MODEL",
            DEFAULT_OLLAMA_MODEL,
        ).strip()

        if not model:
            model = DEFAULT_OLLAMA_MODEL

        base_url = environment.get(
            "OLLAMA_BASE_URL",
            DEFAULT_OLLAMA_BASE_URL,
        ).strip()

        if not base_url:
            base_url = DEFAULT_OLLAMA_BASE_URL

        return LlmProviderRuntimeConfig(
            provider="ollama",
            model=model,
            api_key=None,
            base_url=base_url,
        )

    raise LlmProviderConfigurationError("LLM_PROVIDER must be one of: gemini, ollama.")


def create_llm_adapter(
    config: LlmProviderRuntimeConfig,
) -> LlmAdapter:
    """Create the concrete adapter selected by runtime configuration."""

    if config.provider == "gemini":
        if config.api_key is None:
            raise LlmProviderConfigurationError("Gemini runtime requires an API key.")

        return GeminiLlmAdapter(
            api_key=config.api_key,
            model=config.model,
        )

    if config.provider == "ollama":
        if config.base_url is None:
            raise LlmProviderConfigurationError("Ollama runtime requires a base URL.")

        return OpenAiCompatibleLlmAdapter(
            base_url=config.base_url,
            model=config.model,
        )

    raise LlmProviderConfigurationError(f"Unsupported LLM provider: {config.provider}")
