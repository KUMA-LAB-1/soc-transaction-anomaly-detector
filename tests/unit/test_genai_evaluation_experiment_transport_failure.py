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


class TimeoutOnSecondAdapter:
    def __init__(self):
        self.call_count = 0

    def generate(self, request):
        self.call_count += 1

        if self.call_count == 2:
            raise requests.ReadTimeout(
                "read timeout",
            )

        return LlmResponse(
            content=SUCCESS_RESPONSE,
        )


class TimeoutOnSecondFactory:
    def __init__(self):
        self.adapter = TimeoutOnSecondAdapter()

    def __call__(self, *, api_key, model):
        return self.adapter


def test_experimento_registra_read_timeout_no_checkpoint(
    tmp_path,
):
    output_path = tmp_path / "evaluation.json"
    factory = TimeoutOnSecondFactory()

    with pytest.raises(
        requests.ReadTimeout,
    ):
        run_gemini_evaluation_experiment(
            environment={
                "GEMINI_API_KEY": "segredo-de-teste",
                "GEMINI_MODEL": "gemini-test",
            },
            output_path=output_path,
            generated_at="2026-09-21T07:30:00-03:00",
            adapter_factory=factory,
        )

    assert factory.adapter.call_count == 2
    assert output_path.exists()

    artifact = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert artifact["experiment_status"] == "partial"

    assert artifact["completed_case_ids"] == [
        "ALT-EVAL-001",
    ]

    assert artifact["summary"]["execution_count"] == 1

    assert artifact["failure"] == {
        "case_id": "ALT-EVAL-002",
        "error_type": "ReadTimeout",
        "status_code": None,
    }
