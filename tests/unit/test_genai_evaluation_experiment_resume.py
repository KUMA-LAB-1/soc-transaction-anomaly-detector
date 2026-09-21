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


class FailOnThirdAdapter:
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


class FailOnThirdFactory:
    def __init__(self):
        self.adapter = FailOnThirdAdapter()

    def __call__(self, *, api_key, model):
        return self.adapter


class RecordingSuccessAdapter:
    def __init__(self):
        self.requests = []

    def generate(self, request):
        self.requests.append(request)

        return LlmResponse(
            content=SUCCESS_RESPONSE,
        )


class RecordingSuccessFactory:
    def __init__(self):
        self.adapter = RecordingSuccessAdapter()

    def __call__(self, *, api_key, model):
        return self.adapter


def test_resume_reaproveita_casos_concluidos_e_executa_so_pendentes(
    tmp_path,
):
    output_path = tmp_path / "evaluation.json"
    failing_factory = FailOnThirdFactory()

    with pytest.raises(requests.HTTPError):
        run_gemini_evaluation_experiment(
            environment={
                "GEMINI_API_KEY": "segredo-de-teste",
                "GEMINI_MODEL": "gemini-test",
            },
            output_path=output_path,
            generated_at="2026-09-21T07:00:00-03:00",
            adapter_factory=failing_factory,
        )

    partial = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    assert partial["completed_case_ids"] == [
        "ALT-EVAL-001",
        "ALT-EVAL-002",
    ]

    resume_factory = RecordingSuccessFactory()

    artifact = run_gemini_evaluation_experiment(
        environment={
            "GEMINI_API_KEY": "segredo-de-teste",
            "GEMINI_MODEL": "gemini-test",
        },
        output_path=output_path,
        generated_at="2026-09-21T07:30:00-03:00",
        adapter_factory=resume_factory,
        resume=True,
    )

    assert len(resume_factory.adapter.requests) == 3

    assert artifact["experiment_status"] == "completed"
    assert artifact["failure"] is None

    assert artifact["completed_case_ids"] == [
        "ALT-EVAL-001",
        "ALT-EVAL-002",
        "ALT-EVAL-003",
        "ALT-EVAL-004",
        "ALT-EVAL-005",
    ]

    assert artifact["summary"]["execution_count"] == 5

    assert [execution["case_id"] for execution in artifact["executions"]] == [
        "ALT-EVAL-001",
        "ALT-EVAL-002",
        "ALT-EVAL-003",
        "ALT-EVAL-004",
        "ALT-EVAL-005",
    ]


def test_resume_preserva_respostas_anteriores(
    tmp_path,
):
    output_path = tmp_path / "evaluation.json"
    failing_factory = FailOnThirdFactory()

    with pytest.raises(requests.HTTPError):
        run_gemini_evaluation_experiment(
            environment={
                "GEMINI_API_KEY": "segredo-de-teste",
                "GEMINI_MODEL": "gemini-test",
            },
            output_path=output_path,
            generated_at="2026-09-21T07:00:00-03:00",
            adapter_factory=failing_factory,
        )

    before = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    previous_responses = [
        execution["response_text"] for execution in before["executions"]
    ]

    resume_factory = RecordingSuccessFactory()

    artifact = run_gemini_evaluation_experiment(
        environment={
            "GEMINI_API_KEY": "segredo-de-teste",
            "GEMINI_MODEL": "gemini-test",
        },
        output_path=output_path,
        generated_at="2026-09-21T07:30:00-03:00",
        adapter_factory=resume_factory,
        resume=True,
    )

    assert [
        execution["response_text"] for execution in artifact["executions"][:2]
    ] == previous_responses
