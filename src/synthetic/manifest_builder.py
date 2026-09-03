from datetime import datetime
from typing import TYPE_CHECKING

from .allocation import allocate_scenario_quantities
from .label_policy import OperationalLabelPolicy
from .manifest import (
    DatasetManifest,
    LabelPolicyManifest,
    ScenarioManifestEntry,
)

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
