from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

import requests

from src.genai.contracts import LlmAdapter
from src.genai.evaluation_artifact import build_evaluation_artifact
from src.genai.evaluation_cases import build_generative_evaluation_cases
from src.genai.evaluation_runner import (
    GenerativeEvaluationExecution,
    GenerativeEvaluationRun,
    run_generative_evaluation,
)
from src.genai.evaluation_summary import summarize_generative_run
from src.genai.providers.gemini import GeminiLlmAdapter
from src.genai.response_evaluation import (
    CriterionEvaluation,
    EvaluationVerdict,
    GenerativeResponseEvaluation,
)
from src.genai.runtime import load_genai_runtime_config


def _persist_experiment_artifact(
    *,
    executions: list[GenerativeEvaluationExecution],
    output_path: Path,
    provider: str,
    model: str,
    generated_at: str,
    experiment_status: str,
    failure: dict | None,
) -> dict:
    """Persiste o estado auditável corrente do experimento."""

    run = GenerativeEvaluationRun(
        executions=tuple(executions),
    )

    summary = summarize_generative_run(run)

    artifact = build_evaluation_artifact(
        run,
        summary=summary,
        provider=provider,
        model=model,
        generated_at=generated_at,
    )

    artifact["experiment_status"] = experiment_status
    artifact["completed_case_ids"] = [execution.case_id for execution in executions]
    artifact["failure"] = failure

    output_path.write_text(
        json.dumps(
            artifact,
            ensure_ascii=False,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    return artifact


def _load_checkpoint_executions(
    output_path: Path,
) -> list[GenerativeEvaluationExecution]:
    """Reconstrói execuções já persistidas em um checkpoint."""

    if not output_path.exists():
        return []

    artifact = json.loads(
        output_path.read_text(
            encoding="utf-8",
        )
    )

    executions = []

    for stored_execution in artifact.get(
        "executions",
        (),
    ):
        criteria = tuple(
            CriterionEvaluation(
                name=criterion["name"],
                verdict=EvaluationVerdict(
                    criterion["verdict"],
                ),
                reason=criterion["reason"],
            )
            for criterion in stored_execution.get(
                "criteria",
                (),
            )
        )

        response_text = stored_execution["response_text"]
        case_id = stored_execution["case_id"]

        evaluation = GenerativeResponseEvaluation(
            case_id=case_id,
            response_text=response_text,
            criteria=criteria,
        )

        executions.append(
            GenerativeEvaluationExecution(
                case_id=case_id,
                response_text=response_text,
                evaluation=evaluation,
            )
        )

    return executions


def run_gemini_evaluation_experiment(
    *,
    environment: Mapping[str, str],
    output_path: Path,
    generated_at: str,
    adapter_factory: Callable[..., LlmAdapter] = GeminiLlmAdapter,
    resume: bool = False,
) -> dict:
    """Executa ou retoma o catálogo generativo com checkpoints por caso."""

    config = load_genai_runtime_config(environment)

    adapter = adapter_factory(
        api_key=config.gemini_api_key,
        model=config.gemini_model,
    )

    cases = build_generative_evaluation_cases()

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    executions = (
        _load_checkpoint_executions(
            output_path,
        )
        if resume
        else []
    )

    completed_case_ids = {execution.case_id for execution in executions}

    for case in cases:
        if case.case_id in completed_case_ids:
            continue

        try:
            case_run = run_generative_evaluation(
                adapter,
                cases=(case,),
            )
        except requests.RequestException as exc:
            response = exc.response

            status_code = response.status_code if response is not None else None

            _persist_experiment_artifact(
                executions=executions,
                output_path=output_path,
                provider="gemini",
                model=config.gemini_model,
                generated_at=generated_at,
                experiment_status="partial",
                failure={
                    "case_id": case.case_id,
                    "error_type": type(exc).__name__,
                    "status_code": status_code,
                },
            )

            raise

        executions.extend(
            case_run.executions,
        )

        completed_case_ids.add(
            case.case_id,
        )

        _persist_experiment_artifact(
            executions=executions,
            output_path=output_path,
            provider="gemini",
            model=config.gemini_model,
            generated_at=generated_at,
            experiment_status="partial",
            failure=None,
        )

    return _persist_experiment_artifact(
        executions=executions,
        output_path=output_path,
        provider="gemini",
        model=config.gemini_model,
        generated_at=generated_at,
        experiment_status="completed",
        failure=None,
    )
