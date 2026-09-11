from dataclasses import dataclass
from datetime import datetime

from .benchmark import (
    ScenarioSeparationBenchmarkEntry,
    summarize_scenario_separation_comparisons,
)
from .composer import ScenarioMix
from .dataset import (
    generate_synthetic_dataset,
    generate_synthetic_dataset_v3,
)
from .dataset_comparison import (
    ScenarioSeparationComparisonEntry,
    compare_synthetic_dataset_scenario_separation,
)
from .generation_config import SyntheticGenerationConfig
from .label_policy import OperationalLabelPolicy
from .manifest import DatasetManifest


@dataclass(frozen=True, slots=True)
class ScenarioSeparationBenchmarkRun:
    seed: int
    reference_manifest: DatasetManifest
    candidate_manifest: DatasetManifest
    comparisons: tuple[ScenarioSeparationComparisonEntry, ...]


@dataclass(frozen=True, slots=True)
class ScenarioSeparationBenchmarkResult:
    runs: tuple[ScenarioSeparationBenchmarkRun, ...]
    summary: tuple[ScenarioSeparationBenchmarkEntry, ...]


def run_synthetic_scenario_separation_benchmark(
    *,
    seeds: tuple[int, ...],
    quantidade: int,
    inicio: datetime,
    fim: datetime,
    misturas: list[ScenarioMix],
    label_policy: OperationalLabelPolicy,
    generation_config: SyntheticGenerationConfig,
) -> ScenarioSeparationBenchmarkResult:
    if len(seeds) != len(set(seeds)):
        raise ValueError("seeds nao pode conter valores duplicados.")

    runs: list[ScenarioSeparationBenchmarkRun] = []
    comparisons_by_run: list[tuple[ScenarioSeparationComparisonEntry, ...]] = []

    for seed in seeds:
        reference = generate_synthetic_dataset(
            seed=seed,
            quantidade=quantidade,
            inicio=inicio,
            fim=fim,
            misturas=misturas,
            label_policy=label_policy,
        )

        candidate = generate_synthetic_dataset_v3(
            seed=seed,
            quantidade=quantidade,
            inicio=inicio,
            fim=fim,
            misturas=misturas,
            label_policy=label_policy,
            generation_config=generation_config,
        )

        comparisons = compare_synthetic_dataset_scenario_separation(
            reference,
            candidate,
        )

        runs.append(
            ScenarioSeparationBenchmarkRun(
                seed=seed,
                reference_manifest=reference.manifest,
                candidate_manifest=candidate.manifest,
                comparisons=comparisons,
            )
        )

        comparisons_by_run.append(comparisons)

    summary = summarize_scenario_separation_comparisons(tuple(comparisons_by_run))

    return ScenarioSeparationBenchmarkResult(
        runs=tuple(runs),
        summary=summary,
    )
