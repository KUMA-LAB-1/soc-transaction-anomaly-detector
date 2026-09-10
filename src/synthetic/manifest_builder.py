from datetime import datetime
from typing import TYPE_CHECKING

from .allocation import allocate_scenario_quantities
from .generation_config import SyntheticGenerationConfig
from .generation_manifest_builder import build_synthetic_generation_manifest
from .label_policy import OperationalLabelPolicy
from .manifest import (
    DatasetManifest,
    DatasetManifestV2,
    LabelPolicyManifest,
    ScenarioManifestEntry,
)
from .seed_strategy import SyntheticSeedPlan

if TYPE_CHECKING:
    from .composer import ScenarioMix


def build_dataset_manifest(
    *,
    seed: int,
    quantidade: int,
    inicio: datetime,
    fim: datetime,
    misturas: list["ScenarioMix"],
    label_policy: OperationalLabelPolicy,
) -> DatasetManifest:
    quantidades = allocate_scenario_quantities(
        [mistura.proporcao for mistura in misturas],
        quantidade=quantidade,
    )

    scenarios = tuple(
        ScenarioManifestEntry(
            scenario=mistura.cenario.name,
            configured_proportion=mistura.proporcao,
            allocated_quantity=quantidade_cenario,
        )
        for mistura, quantidade_cenario in zip(
            misturas,
            quantidades,
            strict=True,
        )
    )

    label_policy_manifest = LabelPolicyManifest(
        false_positive_probability=label_policy.probabilidade_falso_positivo,
        false_negative_probability=label_policy.probabilidade_falso_negativo,
    )

    return DatasetManifest(
        schema_version="1",
        seed=seed,
        quantidade=quantidade,
        inicio=inicio,
        fim=fim,
        scenarios=scenarios,
        label_policy=label_policy_manifest,
    )


def build_dataset_manifest_v2(
    *,
    seed_plan: SyntheticSeedPlan,
    quantidade: int,
    inicio: datetime,
    fim: datetime,
    misturas: list["ScenarioMix"],
    label_policy: OperationalLabelPolicy,
    generation_config: SyntheticGenerationConfig,
) -> DatasetManifestV2:
    if not isinstance(seed_plan, SyntheticSeedPlan):
        raise ValueError("seed_plan deve ser SyntheticSeedPlan.")

    base_manifest = build_dataset_manifest(
        seed=seed_plan.root_seed,
        quantidade=quantidade,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
    )

    generation = build_synthetic_generation_manifest(
        config=generation_config,
        seed_plan=seed_plan,
    )

    return DatasetManifestV2(
        schema_version="2",
        seed=base_manifest.seed,
        quantidade=base_manifest.quantidade,
        inicio=base_manifest.inicio,
        fim=base_manifest.fim,
        scenarios=base_manifest.scenarios,
        label_policy=base_manifest.label_policy,
        generation=generation,
    )
