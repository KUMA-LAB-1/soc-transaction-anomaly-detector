import math
from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from src.synthetic.manifest import (
    DatasetManifest,
    LabelPolicyManifest,
    ScenarioManifestEntry,
)

INICIO = datetime(2026, 1, 1, 0, 0)
FIM = datetime(2026, 1, 8, 0, 0)


LABEL_POLICY_SEM_RUIDO = LabelPolicyManifest(
    false_positive_probability=0.0,
    false_negative_probability=0.0,
)


def test_manifest_registra_snapshot_minimo_da_composicao():
    scenarios = (
        ScenarioManifestEntry(
            scenario="baseline",
            configured_proportion=0.70,
            allocated_quantity=7,
        ),
        ScenarioManifestEntry(
            scenario="credential_attack",
            configured_proportion=0.30,
            allocated_quantity=3,
        ),
    )

    manifest = DatasetManifest(
        schema_version="1",
        seed=2026,
        quantidade=10,
        inicio=INICIO,
        fim=FIM,
        label_policy=LABEL_POLICY_SEM_RUIDO,
        scenarios=scenarios,
    )

    assert manifest.schema_version == "1"
    assert manifest.seed == 2026
    assert manifest.quantidade == 10
    assert manifest.inicio == INICIO
    assert manifest.fim == FIM
    assert manifest.scenarios == scenarios


def test_manifest_e_entries_sao_imutaveis():
    entry = ScenarioManifestEntry(
        scenario="baseline",
        configured_proportion=1.0,
        allocated_quantity=10,
    )

    manifest = DatasetManifest(
        schema_version="1",
        seed=42,
        quantidade=10,
        inicio=INICIO,
        fim=FIM,
        label_policy=LABEL_POLICY_SEM_RUIDO,
        scenarios=(entry,),
    )

    with pytest.raises(FrozenInstanceError):
        setattr(entry, "allocated_quantity", 20)

    with pytest.raises(FrozenInstanceError):
        setattr(manifest, "seed", 99)


@pytest.mark.parametrize(
    "scenario",
    [
        "",
        "   ",
        None,
        123,
    ],
)
def test_scenario_manifest_entry_rejeita_nome_invalido(scenario):
    with pytest.raises(ValueError, match="scenario"):
        ScenarioManifestEntry(
            scenario=scenario,
            configured_proportion=1.0,
            allocated_quantity=10,
        )


@pytest.mark.parametrize(
    "configured_proportion",
    [
        0.0,
        -0.01,
        1.01,
        math.nan,
        math.inf,
        -math.inf,
        True,
        False,
        "0.50",
        None,
    ],
)
def test_scenario_manifest_entry_rejeita_proporcao_invalida(
    configured_proportion,
):
    with pytest.raises(ValueError, match="configured_proportion"):
        ScenarioManifestEntry(
            scenario="baseline",
            configured_proportion=configured_proportion,
            allocated_quantity=10,
        )


@pytest.mark.parametrize(
    "allocated_quantity",
    [
        -1,
        True,
        1.5,
        "10",
        None,
    ],
)
def test_scenario_manifest_entry_rejeita_quantidade_alocada_invalida(
    allocated_quantity,
):
    with pytest.raises(ValueError, match="allocated_quantity"):
        ScenarioManifestEntry(
            scenario="baseline",
            configured_proportion=1.0,
            allocated_quantity=allocated_quantity,
        )


@pytest.mark.parametrize(
    "schema_version",
    [
        "",
        "   ",
        None,
        1,
    ],
)
def test_dataset_manifest_rejeita_schema_version_invalida(schema_version):
    with pytest.raises(ValueError, match="schema_version"):
        DatasetManifest(
            schema_version=schema_version,
            seed=42,
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=10,
                ),
            ),
        )


@pytest.mark.parametrize(
    "seed",
    [
        -1,
        True,
        False,
        1.5,
        "42",
        None,
    ],
)
def test_dataset_manifest_rejeita_seed_invalida(seed):
    with pytest.raises(ValueError, match="seed"):
        DatasetManifest(
            schema_version="1",
            seed=seed,
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=10,
                ),
            ),
        )


def test_dataset_manifest_aceita_seed_zero():
    manifest = DatasetManifest(
        schema_version="1",
        seed=0,
        quantidade=10,
        inicio=INICIO,
        fim=FIM,
        label_policy=LABEL_POLICY_SEM_RUIDO,
        scenarios=(
            ScenarioManifestEntry(
                scenario="baseline",
                configured_proportion=1.0,
                allocated_quantity=10,
            ),
        ),
    )

    assert manifest.seed == 0


@pytest.mark.parametrize(
    "quantidade",
    [
        0,
        -1,
        True,
        False,
        1.5,
        "10",
        None,
    ],
)
def test_dataset_manifest_rejeita_quantidade_invalida(quantidade):
    with pytest.raises(ValueError, match="quantidade"):
        DatasetManifest(
            schema_version="1",
            seed=42,
            quantidade=quantidade,
            inicio=INICIO,
            fim=FIM,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=10,
                ),
            ),
        )


@pytest.mark.parametrize(
    ("inicio", "fim"),
    [
        ("2026-01-01", FIM),
        (None, FIM),
        (INICIO, "2026-01-08"),
        (INICIO, None),
    ],
)
def test_dataset_manifest_rejeita_janela_com_tipo_invalido(inicio, fim):
    with pytest.raises(ValueError, match="inicio|fim"):
        DatasetManifest(
            schema_version="1",
            seed=42,
            quantidade=10,
            inicio=inicio,
            fim=fim,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=10,
                ),
            ),
        )


@pytest.mark.parametrize(
    ("inicio", "fim"),
    [
        (INICIO, INICIO),
        (FIM, INICIO),
    ],
)
def test_dataset_manifest_rejeita_janela_temporal_invalida(inicio, fim):
    with pytest.raises(ValueError, match="fim"):
        DatasetManifest(
            schema_version="1",
            seed=42,
            quantidade=10,
            inicio=inicio,
            fim=fim,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=10,
                ),
            ),
        )


def test_dataset_manifest_rejeita_scenarios_que_nao_sao_tuple():
    with pytest.raises(ValueError, match="scenarios"):
        DatasetManifest(
            schema_version="1",
            seed=42,
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=[
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=1.0,
                    allocated_quantity=10,
                ),
            ],
        )


def test_dataset_manifest_rejeita_scenarios_vazio():
    with pytest.raises(ValueError, match="scenarios"):
        DatasetManifest(
            schema_version="1",
            seed=42,
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=(),
        )


@pytest.mark.parametrize(
    "scenarios",
    [
        ("baseline",),
        (None,),
        (123,),
        (
            ScenarioManifestEntry(
                scenario="baseline",
                configured_proportion=1.0,
                allocated_quantity=10,
            ),
            "credential_attack",
        ),
    ],
)
def test_dataset_manifest_rejeita_item_de_scenario_invalido(scenarios):
    with pytest.raises(ValueError, match="scenarios"):
        DatasetManifest(
            schema_version="1",
            seed=42,
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=scenarios,
        )


@pytest.mark.parametrize(
    "allocated_quantities",
    [
        (6, 3),
        (7, 4),
    ],
)
def test_dataset_manifest_rejeita_soma_alocada_incompativel(
    allocated_quantities,
):
    with pytest.raises(ValueError, match="allocated_quantity|quantidade"):
        DatasetManifest(
            schema_version="1",
            seed=42,
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=0.70,
                    allocated_quantity=allocated_quantities[0],
                ),
                ScenarioManifestEntry(
                    scenario="credential_attack",
                    configured_proportion=0.30,
                    allocated_quantity=allocated_quantities[1],
                ),
            ),
        )


@pytest.mark.parametrize(
    "configured_proportions",
    [
        (0.60, 0.20),
        (0.80, 0.40),
    ],
)
def test_dataset_manifest_rejeita_soma_de_proporcoes_incompativel(
    configured_proportions,
):
    with pytest.raises(ValueError, match="configured_proportion|propor"):
        DatasetManifest(
            schema_version="1",
            seed=42,
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
            label_policy=LABEL_POLICY_SEM_RUIDO,
            scenarios=(
                ScenarioManifestEntry(
                    scenario="baseline",
                    configured_proportion=configured_proportions[0],
                    allocated_quantity=7,
                ),
                ScenarioManifestEntry(
                    scenario="credential_attack",
                    configured_proportion=configured_proportions[1],
                    allocated_quantity=3,
                ),
            ),
        )
