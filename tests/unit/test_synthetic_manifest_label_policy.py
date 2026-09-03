import math
from dataclasses import FrozenInstanceError
from datetime import datetime, timedelta

import pytest

from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.manifest import (
    DatasetManifest,
    LabelPolicyManifest,
    ScenarioManifestEntry,
)


def test_label_policy_manifest_registra_snapshot_da_politica():
    manifest = LabelPolicyManifest(
        false_positive_probability=0.20,
        false_negative_probability=0.30,
    )

    assert manifest.false_positive_probability == 0.20
    assert manifest.false_negative_probability == 0.30


def test_label_policy_manifest_e_imutavel():
    manifest = LabelPolicyManifest(
        false_positive_probability=0.20,
        false_negative_probability=0.30,
    )

    with pytest.raises(FrozenInstanceError):
        setattr(
            manifest,
            "false_positive_probability",
            0.50,
        )


@pytest.mark.parametrize(
    "false_positive_probability",
    [
        -0.01,
        1.01,
        math.nan,
        math.inf,
        -math.inf,
        True,
        False,
        "0.20",
        None,
    ],
)
def test_label_policy_manifest_rejeita_falso_positivo_invalido(
    false_positive_probability,
):
    with pytest.raises(ValueError, match="false_positive_probability"):
        LabelPolicyManifest(
            false_positive_probability=false_positive_probability,
            false_negative_probability=0.30,
        )


@pytest.mark.parametrize(
    "false_negative_probability",
    [
        -0.01,
        1.01,
        math.nan,
        math.inf,
        -math.inf,
        True,
        False,
        "0.30",
        None,
    ],
)
def test_label_policy_manifest_rejeita_falso_negativo_invalido(
    false_negative_probability,
):
    with pytest.raises(ValueError, match="false_negative_probability"):
        LabelPolicyManifest(
            false_positive_probability=0.20,
            false_negative_probability=false_negative_probability,
        )


@pytest.mark.parametrize(
    ("false_positive_probability", "false_negative_probability"),
    [
        (0.0, 0.0),
        (1.0, 1.0),
        (0.0, 1.0),
        (1.0, 0.0),
    ],
)
def test_label_policy_manifest_aceita_limites_validos(
    false_positive_probability,
    false_negative_probability,
):
    manifest = LabelPolicyManifest(
        false_positive_probability=false_positive_probability,
        false_negative_probability=false_negative_probability,
    )

    assert manifest.false_positive_probability == false_positive_probability
    assert manifest.false_negative_probability == false_negative_probability


def test_dataset_manifest_registra_snapshot_da_label_policy():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = inicio + timedelta(days=7)

    label_policy = LabelPolicyManifest(
        false_positive_probability=0.20,
        false_negative_probability=0.30,
    )

    manifest = DatasetManifest(
        schema_version="1",
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
        label_policy=label_policy,
    )

    assert manifest.label_policy is label_policy


@pytest.mark.parametrize(
    "label_policy",
    [
        None,
        "policy",
        123,
        OperationalLabelPolicy(
            probabilidade_falso_positivo=0.20,
            probabilidade_falso_negativo=0.30,
        ),
    ],
)
def test_dataset_manifest_rejeita_label_policy_invalida(label_policy):
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = inicio + timedelta(days=7)

    with pytest.raises(ValueError, match="label_policy"):
        DatasetManifest(
            schema_version="1",
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
            label_policy=label_policy,
        )
