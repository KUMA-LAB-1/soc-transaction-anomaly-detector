from __future__ import annotations

import json
from collections.abc import Callable, Mapping
from pathlib import Path

from src.genai.contracts import LlmAdapter
from src.genai.evaluation_artifact import build_evaluation_artifact
from src.genai.evaluation_cases import build_generative_evaluation_cases
from src.genai.evaluation_runner import run_generative_evaluation
from src.genai.evaluation_summary import summarize_generative_run
from src.genai.providers.gemini import GeminiLlmAdapter
from src.genai.runtime import load_genai_runtime_config


def run_gemini_evaluation_experiment(
    *,
    environment: Mapping[str, str],
    output_path: Path,
    generated_at: str,
    adapter_factory: Callable[..., LlmAdapter] = GeminiLlmAdapter,
) -> dict:
    """Executa o catálogo generativo e persiste um artefato JSON auditável."""

    config = load_genai_runtime_config(environment)

    adapter = adapter_factory(
        api_key=config.gemini_api_key,
        model=config.gemini_model,
    )

    cases = build_generative_evaluation_cases()

    run = run_generative_evaluation(
        adapter,
        cases=cases,
    )

    summary = summarize_generative_run(run)

    artifact = build_evaluation_artifact(
        run,
        summary=summary,
        provider="gemini",
        model=config.gemini_model,
        generated_at=generated_at,
    )

    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

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
