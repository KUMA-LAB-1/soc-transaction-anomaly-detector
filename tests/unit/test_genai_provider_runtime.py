import pytest

from src.genai.provider_runtime import (
    DEFAULT_OLLAMA_BASE_URL,
    DEFAULT_OLLAMA_MODEL,
    LlmProviderConfigurationError,
    create_llm_adapter,
    load_llm_provider_runtime_config,
)
from src.genai.providers.gemini import (
    DEFAULT_GEMINI_MODEL,
    GeminiLlmAdapter,
)
from src.genai.providers.openai_compatible import (
    OpenAiCompatibleLlmAdapter,
)


def test_runtime_ollama_funciona_sem_api_key():
    config = load_llm_provider_runtime_config(
        {
            "LLM_PROVIDER": "ollama",
        }
    )

    assert config.provider == "ollama"
    assert config.model == DEFAULT_OLLAMA_MODEL
    assert config.base_url == DEFAULT_OLLAMA_BASE_URL
    assert config.api_key is None


def test_runtime_ollama_aceita_modelo_e_base_url_customizados():
    config = load_llm_provider_runtime_config(
        {
            "LLM_PROVIDER": "  OLLAMA  ",
            "OLLAMA_MODEL": "modelo-local",
            "OLLAMA_BASE_URL": "http://127.0.0.1:9999/v1/",
        }
    )

    assert config.provider == "ollama"
    assert config.model == "modelo-local"
    assert config.base_url == "http://127.0.0.1:9999/v1/"


def test_runtime_gemini_preserva_configuracao_existente():
    config = load_llm_provider_runtime_config(
        {
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "secret-demo-key",
        }
    )

    assert config.provider == "gemini"
    assert config.model == DEFAULT_GEMINI_MODEL
    assert config.api_key == "secret-demo-key"
    assert config.base_url is None
    assert "secret-demo-key" not in repr(config)


def test_runtime_gemini_exige_api_key():
    with pytest.raises(
        LlmProviderConfigurationError,
        match="GEMINI_API_KEY",
    ):
        load_llm_provider_runtime_config(
            {
                "LLM_PROVIDER": "gemini",
            }
        )


def test_runtime_rejeita_provider_desconhecido():
    with pytest.raises(
        LlmProviderConfigurationError,
        match="LLM_PROVIDER",
    ):
        load_llm_provider_runtime_config(
            {
                "LLM_PROVIDER": "urso-quantico",
            }
        )


def test_factory_cria_adapter_ollama_openai_compatible():
    config = load_llm_provider_runtime_config(
        {
            "LLM_PROVIDER": "ollama",
            "OLLAMA_MODEL": "qwen3:4b-instruct",
            "OLLAMA_BASE_URL": "http://localhost:11434/v1",
        }
    )

    adapter = create_llm_adapter(config)

    assert isinstance(
        adapter,
        OpenAiCompatibleLlmAdapter,
    )


def test_factory_cria_adapter_gemini():
    config = load_llm_provider_runtime_config(
        {
            "LLM_PROVIDER": "gemini",
            "GEMINI_API_KEY": "secret-demo-key",
            "GEMINI_MODEL": "gemini-test",
        }
    )

    adapter = create_llm_adapter(config)

    assert isinstance(
        adapter,
        GeminiLlmAdapter,
    )
