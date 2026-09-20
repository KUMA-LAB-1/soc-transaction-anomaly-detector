import pytest

from src.genai.providers.gemini import DEFAULT_GEMINI_MODEL
from src.genai.runtime import (
    GenAiConfigurationError,
    load_genai_runtime_config,
)


def test_runtime_config_exige_gemini_api_key():
    with pytest.raises(
        GenAiConfigurationError,
        match="GEMINI_API_KEY",
    ):
        load_genai_runtime_config({})


def test_runtime_config_rejeita_api_key_vazia():
    with pytest.raises(
        GenAiConfigurationError,
        match="GEMINI_API_KEY",
    ):
        load_genai_runtime_config(
            {
                "GEMINI_API_KEY": "   ",
            }
        )


def test_runtime_config_usa_modelo_padrao_sem_expor_secret():
    config = load_genai_runtime_config(
        {
            "GEMINI_API_KEY": "secret-demo-key",
        }
    )

    assert config.gemini_api_key == "secret-demo-key"
    assert config.gemini_model == DEFAULT_GEMINI_MODEL
    assert "secret-demo-key" not in repr(config)


def test_runtime_config_aceita_modelo_customizado():
    config = load_genai_runtime_config(
        {
            "GEMINI_API_KEY": "secret-demo-key",
            "GEMINI_MODEL": "gemini-custom-model",
        }
    )

    assert config.gemini_model == "gemini-custom-model"
