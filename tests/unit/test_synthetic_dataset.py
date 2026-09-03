from collections import Counter
from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import (
    GeneratedSyntheticDataset,
    generate_synthetic_dataset,
)
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario


def test_generate_synthetic_dataset_entrega_registros_e_manifest_coerentes():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=1 / 3,
        ),
        ScenarioMix(
            cenario=obter_cenario("credential_attack"),
            proporcao=1 / 3,
        ),
        ScenarioMix(
            cenario=obter_cenario("account_takeover"),
            proporcao=1 / 3,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.20,
        probabilidade_falso_negativo=0.30,
    )

    resultado = generate_synthetic_dataset(
        seed=42,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
    )

    assert isinstance(resultado, GeneratedSyntheticDataset)
    assert isinstance(resultado.records, tuple)
    assert len(resultado.records) == 10

    contagem_por_cenario = Counter(
        registro.truth.scenario for registro in resultado.records
    )

    assert contagem_por_cenario == {
        "baseline": 4,
        "credential_attack": 3,
        "account_takeover": 3,
    }

    assert tuple(
        (entry.scenario, entry.allocated_quantity)
        for entry in resultado.manifest.scenarios
    ) == (
        ("baseline", 4),
        ("credential_attack", 3),
        ("account_takeover", 3),
    )

    assert resultado.manifest.seed == 42
    assert resultado.manifest.quantidade == 10
    assert resultado.manifest.inicio == inicio
    assert resultado.manifest.fim == fim

    assert resultado.manifest.label_policy.false_positive_probability == 0.20
    assert resultado.manifest.label_policy.false_negative_probability == 0.30


def test_generate_synthetic_dataset_e_reprodutivel_com_mesma_configuracao():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=0.70,
        ),
        ScenarioMix(
            cenario=obter_cenario("credential_attack"),
            proporcao=0.30,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.20,
        probabilidade_falso_negativo=0.30,
    )

    primeira_execucao = generate_synthetic_dataset(
        seed=777,
        quantidade=100,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
    )

    segunda_execucao = generate_synthetic_dataset(
        seed=777,
        quantidade=100,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
    )

    assert primeira_execucao.records == segunda_execucao.records
    assert primeira_execucao.manifest == segunda_execucao.manifest


def test_generated_synthetic_dataset_e_estruturalmente_imutavel():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    resultado = generate_synthetic_dataset(
        seed=42,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=1.0,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
    )

    assert isinstance(resultado.records, tuple)
    assert len(resultado.records) == resultado.manifest.quantidade

    with pytest.raises(FrozenInstanceError):
        setattr(resultado, "records", ())


def test_generated_synthetic_dataset_rejeita_quantidade_incompativel_com_manifest():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    resultado = generate_synthetic_dataset(
        seed=42,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=1.0,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
    )

    with pytest.raises(ValueError, match="quantidade"):
        GeneratedSyntheticDataset(
            records=resultado.records[:-1],
            manifest=resultado.manifest,
        )
