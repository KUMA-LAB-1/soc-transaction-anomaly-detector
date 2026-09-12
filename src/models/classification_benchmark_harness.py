from dataclasses import dataclass
from datetime import datetime

from ..synthetic.composer import ScenarioMix
from ..synthetic.dataset import generate_synthetic_dataset_v3
from ..synthetic.generation_config import SyntheticGenerationConfig
from ..synthetic.label_policy import OperationalLabelPolicy
from ..synthetic.manifest import DatasetManifest
from .classification_benchmark import (
    SyntheticClassificationBenchmarkResult,
    run_synthetic_classification_benchmark,
)


@dataclass(frozen=True, slots=True)
class ClassificationBenchmarkRun:
    seed: int
    manifest: DatasetManifest
    benchmark: SyntheticClassificationBenchmarkResult


@dataclass(frozen=True, slots=True)
class ClassificationBenchmarkHarnessResult:
    runs: tuple[ClassificationBenchmarkRun, ...]


def run_synthetic_classification_benchmark_multi_seed(
    *,
    seeds: tuple[int, ...],
    quantidade: int,
    inicio: datetime,
    fim: datetime,
    misturas: list[ScenarioMix],
    label_policy: OperationalLabelPolicy,
    generation_config: SyntheticGenerationConfig,
) -> ClassificationBenchmarkHarnessResult:
    if len(seeds) != len(set(seeds)):
        raise ValueError("seeds nao pode conter valores duplicados.")

    runs: list[ClassificationBenchmarkRun] = []

    for seed in seeds:
        dataset = generate_synthetic_dataset_v3(
            seed=seed,
            quantidade=quantidade,
            inicio=inicio,
            fim=fim,
            misturas=misturas,
            label_policy=label_policy,
            generation_config=generation_config,
        )

        benchmark = run_synthetic_classification_benchmark(
            dataset,
        )

        runs.append(
            ClassificationBenchmarkRun(
                seed=seed,
                manifest=dataset.manifest,
                benchmark=benchmark,
            )
        )

    return ClassificationBenchmarkHarnessResult(
        runs=tuple(runs),
    )
