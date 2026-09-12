from datetime import datetime
from types import SimpleNamespace

import pytest

from src.models.detector_benchmark_harness import (
    DetectorBenchmarkHarnessResult,
    DetectorBenchmarkRun,
    run_synthetic_detector_benchmark_multi_seed,
)


def test_detector_benchmark_harness_orquestra_runs_por_seed(
    monkeypatch,
):
    import src.models.detector_benchmark_harness as harness

    seeds = (11, 29)

    inicio = datetime(2026, 1, 1)
    fim = datetime(2026, 1, 2)

    misturas = [object()]
    label_policy = object()
    generation_config = object()

    manifests = {seed: object() for seed in seeds}

    datasets = {
        seed: SimpleNamespace(
            manifest=manifests[seed],
        )
        for seed in seeds
    }

    benchmark_results = {seed: object() for seed in seeds}

    generation_calls = []
    benchmark_calls = []

    def fake_generate_synthetic_dataset_v3(**kwargs):
        generation_calls.append(kwargs)
        return datasets[kwargs["seed"]]

    def fake_run_synthetic_detector_benchmark(
        dataset,
        *,
        contamination,
    ):
        benchmark_calls.append(
            (
                dataset,
                contamination,
            )
        )

        for seed in seeds:
            if dataset is datasets[seed]:
                return benchmark_results[seed]

        raise AssertionError("dataset inesperado no benchmark")

    monkeypatch.setattr(
        harness,
        "generate_synthetic_dataset_v3",
        fake_generate_synthetic_dataset_v3,
    )
    monkeypatch.setattr(
        harness,
        "run_synthetic_detector_benchmark",
        fake_run_synthetic_detector_benchmark,
    )

    result = run_synthetic_detector_benchmark_multi_seed(
        seeds=seeds,
        quantidade=200,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
        contamination=0.10,
    )

    assert isinstance(
        result,
        DetectorBenchmarkHarnessResult,
    )

    assert tuple(run.seed for run in result.runs) == seeds

    for run, seed in zip(
        result.runs,
        seeds,
        strict=True,
    ):
        assert isinstance(
            run,
            DetectorBenchmarkRun,
        )
        assert run.manifest is manifests[seed]
        assert run.benchmark is benchmark_results[seed]

    assert generation_calls == [
        {
            "seed": 11,
            "quantidade": 200,
            "inicio": inicio,
            "fim": fim,
            "misturas": misturas,
            "label_policy": label_policy,
            "generation_config": generation_config,
        },
        {
            "seed": 29,
            "quantidade": 200,
            "inicio": inicio,
            "fim": fim,
            "misturas": misturas,
            "label_policy": label_policy,
            "generation_config": generation_config,
        },
    ]

    assert benchmark_calls == [
        (
            datasets[11],
            0.10,
        ),
        (
            datasets[29],
            0.10,
        ),
    ]


def test_detector_benchmark_harness_rejeita_seeds_duplicadas(
    monkeypatch,
):
    import src.models.detector_benchmark_harness as harness

    def unexpected_generation(**kwargs):
        raise AssertionError(
            f"geracao nao deveria ocorrer para seeds duplicadas: {kwargs}"
        )

    monkeypatch.setattr(
        harness,
        "generate_synthetic_dataset_v3",
        unexpected_generation,
    )

    with pytest.raises(
        ValueError,
        match="seeds nao pode conter valores duplicados",
    ):
        run_synthetic_detector_benchmark_multi_seed(
            seeds=(11, 11),
            quantidade=200,
            inicio=datetime(2026, 1, 1),
            fim=datetime(2026, 1, 2),
            misturas=[object()],
            label_policy=object(),
            generation_config=object(),
            contamination=0.10,
        )
