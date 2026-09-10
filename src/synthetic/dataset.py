from dataclasses import dataclass
from datetime import datetime

from .composer import MixedDatasetComposer, ScenarioMix
from .contracts import SyntheticRecord
from .generation_config import SyntheticGenerationConfig
from .label_policy import OperationalLabelPolicy
from .manifest import DatasetManifest
from .manifest_builder import build_dataset_manifest, build_dataset_manifest_v2
from .population_generation import PopulationGenerator
from .seed_strategy import build_synthetic_seed_plan
from .statistical import StatisticalGenerator


@dataclass(frozen=True, slots=True)
class GeneratedSyntheticDataset:
    records: tuple[SyntheticRecord, ...]
    manifest: DatasetManifest

    def __post_init__(self) -> None:
        if len(self.records) != self.manifest.quantidade:
            raise ValueError(
                "a quantidade de records deve ser igual a manifest.quantidade."
            )


def generate_synthetic_dataset(
    *,
    seed: int,
    quantidade: int,
    inicio: datetime,
    fim: datetime,
    misturas: list[ScenarioMix],
    label_policy: OperationalLabelPolicy,
) -> GeneratedSyntheticDataset:
    gerador = StatisticalGenerator(
        seed=seed,
        label_policy=label_policy,
    )

    compositor = MixedDatasetComposer(gerador)

    registros = compositor.compor(
        misturas,
        quantidade=quantidade,
        inicio=inicio,
        fim=fim,
    )

    manifest = build_dataset_manifest(
        seed=seed,
        quantidade=quantidade,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
    )

    return GeneratedSyntheticDataset(
        records=tuple(registros),
        manifest=manifest,
    )


def generate_synthetic_dataset_v3(
    *,
    seed: int,
    quantidade: int,
    inicio: datetime,
    fim: datetime,
    misturas: list[ScenarioMix],
    label_policy: OperationalLabelPolicy,
    generation_config: SyntheticGenerationConfig,
) -> GeneratedSyntheticDataset:
    if not isinstance(
        generation_config,
        SyntheticGenerationConfig,
    ):
        raise ValueError("generation_config deve ser SyntheticGenerationConfig.")

    if generation_config.severity_policy is not None:
        raise ValueError("severity_policy ainda nao esta integrada ao runtime V3.")

    if generation_config.scenario_configs:
        raise ValueError("scenario_configs ainda nao estao integrados ao runtime V3.")

    seed_plan = build_synthetic_seed_plan(seed)

    population = (
        PopulationGenerator(
            seed=seed_plan.population_seed,
        ).generate(generation_config.population_config)
        if generation_config.population_config is not None
        else None
    )

    gerador = StatisticalGenerator(
        seed=seed_plan.statistical_seed,
        label_policy=label_policy,
        population=population,
    )

    compositor = MixedDatasetComposer(gerador)

    registros = compositor.compor(
        quantidade=quantidade,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
    )

    manifest = build_dataset_manifest_v2(
        seed_plan=seed_plan,
        quantidade=quantidade,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    return GeneratedSyntheticDataset(
        records=tuple(registros),
        manifest=manifest,
    )
