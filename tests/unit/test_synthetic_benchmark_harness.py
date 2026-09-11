from datetime import datetime
from types import SimpleNamespace

import pytest

from src.synthetic.benchmark_harness import (
    ScenarioSeparationBenchmarkResult,
    ScenarioSeparationBenchmarkRun,
    run_synthetic_scenario_separation_benchmark,
)


def test_run_synthetic_scenario_separation_benchmark_orchestrates_multi_seed_runs(
    monkeypatch,
) -> None:
    import src.synthetic.benchmark_harness as benchmark_harness

    seeds = (11, 29)

    inicio = datetime(2026, 1, 1)
    fim = datetime(2026, 1, 2)

    misturas = [object()]
    label_policy = object()
    generation_config = object()

    reference_manifests = {seed: object() for seed in seeds}
    candidate_manifests = {seed: object() for seed in seeds}

    reference_datasets = {
        seed: SimpleNamespace(
            manifest=reference_manifests[seed],
        )
        for seed in seeds
    }
    candidate_datasets = {
        seed: SimpleNamespace(
            manifest=candidate_manifests[seed],
        )
        for seed in seeds
    }

    comparisons_by_seed = {
        11: ("comparison-11",),
        29: ("comparison-29",),
    }

    expected_summary = ("summary",)

    generation_calls = []

    def fake_generate_synthetic_dataset(**kwargs):
        generation_calls.append(
            (
                "reference",
                kwargs,
            )
        )

        return reference_datasets[kwargs["seed"]]

    def fake_generate_synthetic_dataset_v3(**kwargs):
        generation_calls.append(
            (
                "candidate",
                kwargs,
            )
        )

        return candidate_datasets[kwargs["seed"]]

    def fake_compare_synthetic_dataset_scenario_separation(
        reference,
        candidate,
    ):
        for seed in seeds:
            if reference is reference_datasets[seed]:
                assert candidate is candidate_datasets[seed]
                return comparisons_by_seed[seed]

        raise AssertionError("par de datasets inesperado")

    def fake_summarize_scenario_separation_comparisons(runs):
        assert runs == (
            comparisons_by_seed[11],
            comparisons_by_seed[29],
        )

        return expected_summary

    monkeypatch.setattr(
        benchmark_harness,
        "generate_synthetic_dataset",
        fake_generate_synthetic_dataset,
    )
    monkeypatch.setattr(
        benchmark_harness,
        "generate_synthetic_dataset_v3",
        fake_generate_synthetic_dataset_v3,
    )
    monkeypatch.setattr(
        benchmark_harness,
        "compare_synthetic_dataset_scenario_separation",
        fake_compare_synthetic_dataset_scenario_separation,
    )
    monkeypatch.setattr(
        benchmark_harness,
        "summarize_scenario_separation_comparisons",
        fake_summarize_scenario_separation_comparisons,
    )

    result = run_synthetic_scenario_separation_benchmark(
        seeds=seeds,
        quantidade=200,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    assert isinstance(
        result,
        ScenarioSeparationBenchmarkResult,
    )

    assert tuple(run.seed for run in result.runs) == seeds
    assert result.summary == expected_summary

    for run, seed in zip(
        result.runs,
        seeds,
        strict=True,
    ):
        assert isinstance(
            run,
            ScenarioSeparationBenchmarkRun,
        )
        assert run.reference_manifest is reference_manifests[seed]
        assert run.candidate_manifest is candidate_manifests[seed]
        assert run.comparisons == comparisons_by_seed[seed]

    assert len(generation_calls) == 4

    for index, seed in enumerate(seeds):
        reference_kind, reference_kwargs = generation_calls[index * 2]
        candidate_kind, candidate_kwargs = generation_calls[index * 2 + 1]

        assert reference_kind == "reference"
        assert candidate_kind == "candidate"

        assert reference_kwargs == {
            "seed": seed,
            "quantidade": 200,
            "inicio": inicio,
            "fim": fim,
            "misturas": misturas,
            "label_policy": label_policy,
        }

        assert candidate_kwargs == {
            "seed": seed,
            "quantidade": 200,
            "inicio": inicio,
            "fim": fim,
            "misturas": misturas,
            "label_policy": label_policy,
            "generation_config": generation_config,
        }


def test_run_synthetic_scenario_separation_benchmark_rejects_duplicate_root_seeds(
    monkeypatch,
) -> None:
    import src.synthetic.benchmark_harness as benchmark_harness

    def unexpected_generation(**kwargs):
        raise AssertionError(
            f"geracao nao deveria ocorrer para seeds duplicadas: {kwargs}"
        )

    monkeypatch.setattr(
        benchmark_harness,
        "generate_synthetic_dataset",
        unexpected_generation,
    )
    monkeypatch.setattr(
        benchmark_harness,
        "generate_synthetic_dataset_v3",
        unexpected_generation,
    )

    with pytest.raises(
        ValueError,
        match="seeds nao pode conter valores duplicados",
    ):
        benchmark_harness.run_synthetic_scenario_separation_benchmark(
            seeds=(11, 11),
            quantidade=200,
            inicio=datetime(2026, 1, 1),
            fim=datetime(2026, 1, 2),
            misturas=[object()],
            label_policy=object(),
            generation_config=object(),
        )
