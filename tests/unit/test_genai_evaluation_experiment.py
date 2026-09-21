import json

import pytest

from src.genai.contracts import LlmResponse
from src.genai.evaluation_experiment import run_gemini_evaluation_experiment
from src.genai.runtime import GenAiConfigurationError


class DeterministicAdapter:
    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)

        return LlmResponse(
            content=(
                "O incidente não está confirmado. "
                "É necessário coletar e verificar as evidências ausentes."
            )
        )


class RecordingAdapterFactory:
    def __init__(self):
        self.calls = []
        self.adapter = DeterministicAdapter()

    def __call__(self, *, api_key, model):
        self.calls.append(
            {
                "api_key": api_key,
                "model": model,
            }
        )
        return self.adapter


def test_experimento_executa_catalogo_e_grava_json(tmp_path):
    output_path = tmp_path / "generative-evaluation.json"
    factory = RecordingAdapterFactory()

    artifact = run_gemini_evaluation_experiment(
        environment={
            "GEMINI_API_KEY": "segredo-de-teste",
            "GEMINI_MODEL": "gemini-test",
        },
        output_path=output_path,
        generated_at="2026-09-20T18:00:00-03:00",
        adapter_factory=factory,
    )

    assert factory.calls == [
        {
            "api_key": "segredo-de-teste",
            "model": "gemini-test",
        }
    ]

    assert len(factory.adapter.requests) == 5

    assert artifact["provider"] == "gemini"
    assert artifact["model"] == "gemini-test"
    assert artifact["summary"]["execution_count"] == 5

    assert output_path.exists()

    persisted = json.loads(output_path.read_text(encoding="utf-8"))

    assert persisted == artifact


def test_experimento_nao_persiste_api_key(tmp_path):
    output_path = tmp_path / "generative-evaluation.json"
    factory = RecordingAdapterFactory()

    run_gemini_evaluation_experiment(
        environment={
            "GEMINI_API_KEY": "segredo-super-sensivel",
            "GEMINI_MODEL": "gemini-test",
        },
        output_path=output_path,
        generated_at="2026-09-20T18:00:00-03:00",
        adapter_factory=factory,
    )

    persisted = output_path.read_text(encoding="utf-8")

    assert "segredo-super-sensivel" not in persisted
    assert "GEMINI_API_KEY" not in persisted


def test_experimento_cria_diretorio_de_saida(tmp_path):
    output_path = tmp_path / "nested" / "evaluation" / "result.json"

    factory = RecordingAdapterFactory()

    run_gemini_evaluation_experiment(
        environment={
            "GEMINI_API_KEY": "segredo-de-teste",
        },
        output_path=output_path,
        generated_at="2026-09-20T18:00:00-03:00",
        adapter_factory=factory,
    )

    assert output_path.exists()


def test_experimento_rejeita_configuracao_sem_api_key(tmp_path):
    output_path = tmp_path / "result.json"
    factory = RecordingAdapterFactory()

    with pytest.raises(
        GenAiConfigurationError,
        match="GEMINI_API_KEY",
    ):
        run_gemini_evaluation_experiment(
            environment={},
            output_path=output_path,
            generated_at="2026-09-20T18:00:00-03:00",
            adapter_factory=factory,
        )

    assert not output_path.exists()
    assert factory.calls == []
