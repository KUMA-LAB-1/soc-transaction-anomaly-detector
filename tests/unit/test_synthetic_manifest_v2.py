from datetime import datetime

import pytest

from src.synthetic.generation_manifest import (
    SeedStrategyManifest,
    SyntheticGenerationManifest,
)
from src.synthetic.manifest import (
    DatasetManifestV2,
    LabelPolicyManifest,
    ScenarioManifestEntry,
)


def test_dataset_manifest_v2_registra_generation_provenance():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    generation = SyntheticGenerationManifest(
        seed_strategy=SeedStrategyManifest(
            strategy_version="1",
            statistical_seed=101,
            population_seed=202,
        ),
    )

    manifest = DatasetManifestV2(
        schema_version="2",
        seed=42,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        scenarios=(
            ScenarioManifestEntry(
                scenario="baseline",
                configured_proportion=1.0,
                allocated_quantity=10,
            ),
        ),
        label_policy=LabelPolicyManifest(
            false_positive_probability=0.0,
            false_negative_probability=0.0,
        ),
        generation=generation,
    )

    assert manifest.schema_version == "2"
    assert manifest.seed == 42
    assert manifest.quantidade == 10
    assert manifest.inicio == inicio
    assert manifest.fim == fim
    assert manifest.generation is generation


def test_dataset_manifest_v2_rejeita_schema_version_diferente_de_2():
    generation = SyntheticGenerationManifest(
        seed_strategy=SeedStrategyManifest(
            strategy_version="1",
            statistical_seed=101,
            population_seed=202,
        ),
    )

    with pytest.raises(ValueError, match="schema_version"):
        DatasetManifestV2(
            schema_version="1",
            seed=42,
            quantidade=10,
            inicio=datetime(2026, 1, 1, 0, 0),
            fim=datetime(2026, 1, 8, 0, 0),
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=10,
                ),
            ),
            label_policy=LabelPolicyManifest(
                false_positive_probability=0.0,
                false_negative_probability=0.0,
            ),
            generation=generation,
        )


@pytest.mark.parametrize(
    "generation",
    (
        123,
        "generation",
        object(),
        None,
    ),
)
def test_dataset_manifest_v2_rejeita_generation_invalida(
    generation,
):
    with pytest.raises(ValueError, match="generation"):
        DatasetManifestV2(
            schema_version="2",
            seed=42,
            quantidade=10,
            inicio=datetime(2026, 1, 1, 0, 0),
            fim=datetime(2026, 1, 8, 0, 0),
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=10,
                ),
            ),
            label_policy=LabelPolicyManifest(
                false_positive_probability=0.0,
                false_negative_probability=0.0,
            ),
            generation=generation,
        )


def test_dataset_manifest_v2_mantem_contrato_de_dataset_manifest():
    from src.synthetic.manifest import DatasetManifest

    generation = SyntheticGenerationManifest(
        seed_strategy=SeedStrategyManifest(
            strategy_version="1",
            statistical_seed=101,
            population_seed=202,
        ),
    )

    manifest = DatasetManifestV2(
        schema_version="2",
        seed=42,
        quantidade=10,
        inicio=datetime(2026, 1, 1, 0, 0),
        fim=datetime(2026, 1, 8, 0, 0),
        scenarios=(
            ScenarioManifestEntry(
                scenario="baseline",
                configured_proportion=1.0,
                allocated_quantity=10,
            ),
        ),
        label_policy=LabelPolicyManifest(
            false_positive_probability=0.0,
            false_negative_probability=0.0,
        ),
        generation=generation,
    )

    assert isinstance(manifest, DatasetManifest)


def test_dataset_manifest_v2_e_imutavel():
    from dataclasses import FrozenInstanceError

    generation = SyntheticGenerationManifest(
        seed_strategy=SeedStrategyManifest(
            strategy_version="1",
            statistical_seed=101,
            population_seed=202,
        ),
    )

    manifest = DatasetManifestV2(
        schema_version="2",
        seed=42,
        quantidade=10,
        inicio=datetime(2026, 1, 1, 0, 0),
        fim=datetime(2026, 1, 8, 0, 0),
        scenarios=(
            ScenarioManifestEntry(
                scenario="baseline",
                configured_proportion=1.0,
                allocated_quantity=10,
            ),
        ),
        label_policy=LabelPolicyManifest(
            false_positive_probability=0.0,
            false_negative_probability=0.0,
        ),
        generation=generation,
    )

    with pytest.raises(FrozenInstanceError):
        manifest.generation = generation


def test_dataset_manifest_v2_preserva_validacoes_do_dataset_manifest():
    generation = SyntheticGenerationManifest(
        seed_strategy=SeedStrategyManifest(
            strategy_version="1",
            statistical_seed=101,
            population_seed=202,
        ),
    )

    with pytest.raises(ValueError, match="quantidade"):
        DatasetManifestV2(
            schema_version="2",
            seed=42,
            quantidade=0,
            inicio=datetime(2026, 1, 1, 0, 0),
            fim=datetime(2026, 1, 8, 0, 0),
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=0,
                ),
            ),
            label_policy=LabelPolicyManifest(
                false_positive_probability=0.0,
                false_negative_probability=0.0,
            ),
            generation=generation,
        )
