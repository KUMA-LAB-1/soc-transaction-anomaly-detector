import json

import pytest
import requests

from src.genai.contracts import LlmResponse
from src.genai.evaluation_experiment import (
    run_gemini_evaluation_experiment,
)

SUCCESS_RESPONSE = (
    "O incidente não está confirmado. "
    "É necessário coletar e verificar as evidências ausentes."
)


class PartialFailureAdapter:
    def __init__(self):
        self.call_count = 0

    def generate(self, request):
        self.call_count += 1

        if self.call_count == 3:
            response = requests.Response()
            response.status_code = 429

            raise requests.HTTPError(
                "429 Too Many Requests",
                response=response,
            )

        return LlmResponse(
            content=SUCCESS_RESPONSE,
        )


class PartialFailureFactory:
    def __init__(self):
        self.adapter = PartialFailureAdapter()

    def __call__(self, *, api_key, model):
        return self.adapter


class SuccessfulAdapter:
    def generate(self, request):
        return LlmResponse(
            content=SUCCESS_RESPONSE,
        )


class SuccessfulFactory:
    def __call__(self, *, api_key, model):
        return SuccessfulAdapter()


def test_experimento_preserva_checkpoint_quando_caso_falha(
    tmp_path,
):
    output_path = tmp_path / "partial.json"
    factory = PartialFailureFactory()

    with pytest.raises(requests.HTTPError):
        run_gemini_evaluation_experiment(
            environment={
                "GEMINI_API_KEY": "segredo-de-teste",
                "GEMINI_MODEL": "gemini-test",
            },
            output_path=output_path,
            generated_at="2026-09-21T07:00:00-03:00",
            adapter_factory=factory,
        )

    assert factory.adapter.call_count == 3
    assert output_path.exists()

    artifact = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert artifact["experiment_status"] == "partial"

    assert artifact["completed_case_ids"] == [
        "ALT-EVAL-001",
        "ALT-EVAL-002",
    ]

    assert artifact["summary"]["execution_count"] == 2

    assert artifact["failure"] == {
        "case_id": "ALT-EVAL-003",
        "error_type": "HTTPError",
        "status_code": 429,
    }

    serialized = json.dumps(
        artifact,
        ensure_ascii=False,
    )

    assert "segredo-de-teste" not in serialized


def test_experimento_completo_registra_status_completed(
    tmp_path,
):
    output_path = tmp_path / "completed.json"

    artifact = run_gemini_evaluation_experiment(
        environment={
            "GEMINI_API_KEY": "segredo-de-teste",
            "GEMINI_MODEL": "gemini-test",
        },
        output_path=output_path,
        generated_at="2026-09-21T07:00:00-03:00",
        adapter_factory=SuccessfulFactory(),
    )

    assert artifact["experiment_status"] == "completed"

    assert artifact["completed_case_ids"] == [
        "ALT-EVAL-001",
        "ALT-EVAL-002",
        "ALT-EVAL-003",
        "ALT-EVAL-004",
        "ALT-EVAL-005",
    ]

    assert artifact["failure"] is None
    assert artifact["summary"]["execution_count"] == 5
