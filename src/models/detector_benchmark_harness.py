from dataclasses import dataclass
from datetime import datetime

from ..synthetic.composer import ScenarioMix
from ..synthetic.dataset import generate_synthetic_dataset_v3
from ..synthetic.generation_config import SyntheticGenerationConfig
from ..synthetic.label_policy import OperationalLabelPolicy
from ..synthetic.manifest import DatasetManifest
from .detector_benchmark import (
    SyntheticDetectorBenchmarkResult,
    run_synthetic_detector_benchmark,
)


@dataclass(frozen=True, slots=True)
class DetectorBenchmarkRun:
    seed: int
    manifest: DatasetManifest
    benchmark: SyntheticDetectorBenchmarkResult


@dataclass(frozen=True, slots=True)
class DetectorBenchmarkHarnessResult:
    runs: tuple[DetectorBenchmarkRun, ...]


def run_synthetic_detector_benchmark_multi_seed(
    *,
    seeds: tuple[int, ...],
    quantidade: int,
    inicio: datetime,
    fim: datetime,
    misturas: list[ScenarioMix],
    label_policy: OperationalLabelPolicy,
    generation_config: SyntheticGenerationConfig,
    contamination: float,
) -> DetectorBenchmarkHarnessResult:
    if len(seeds) != len(set(seeds)):
        raise ValueError("seeds nao pode conter valores duplicados.")

    runs: list[DetectorBenchmarkRun] = []

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

        benchmark = run_synthetic_detector_benchmark(
            dataset,
            contamination=contamination,
        )

        runs.append(
            DetectorBenchmarkRun(
                seed=seed,
                manifest=dataset.manifest,
                benchmark=benchmark,
            )
        )

    return DetectorBenchmarkHarnessResult(
        runs=tuple(runs),
    )
