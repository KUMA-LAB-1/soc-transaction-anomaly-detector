from dataclasses import dataclass
from datetime import datetime

from .composer import MixedDatasetComposer, ScenarioMix
from .contracts import SyntheticRecord
from .label_policy import OperationalLabelPolicy
from .manifest import DatasetManifest
from .manifest_builder import build_dataset_manifest
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
