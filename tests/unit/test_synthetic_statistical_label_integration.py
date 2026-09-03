from datetime import datetime, timedelta

import pytest

from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario
from src.synthetic.statistical import StatisticalGenerator

INICIO = datetime(2026, 1, 1, 0, 0)
FIM = INICIO + timedelta(days=7)


def gerar(
    nome_cenario: str,
    politica: OperationalLabelPolicy,
    *,
    seed: int = 42,
    quantidade: int = 100,
):
    gerador = StatisticalGenerator(
        seed=seed,
        label_policy=politica,
    )

    return gerador.gerar_registros(
        obter_cenario(nome_cenario),
        quantidade=quantidade,
        inicio=INICIO,
        fim=FIM,
    )


def test_gerador_aplica_falso_positivo_da_label_policy():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=1.0,
        probabilidade_falso_negativo=0.0,
    )

    registros = gerar(
        "baseline",
        politica,
        quantidade=100,
    )

    statuses = [
        registro.operational_labels["status_transacao"] for registro in registros
    ]

    assert set(statuses) == {"Em Análise"}


def test_gerador_aplica_falso_negativo_da_label_policy():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=1.0,
    )

    registros = gerar(
        "credential_attack",
        politica,
        quantidade=100,
    )

    statuses = [
        registro.operational_labels["status_transacao"] for registro in registros
    ]

    assert set(statuses) == {"Concluída"}


def test_mudar_label_policy_nao_altera_observaveis_nem_ground_truth():
    sem_falso_positivo = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )
    falso_positivo_total = OperationalLabelPolicy(
        probabilidade_falso_positivo=1.0,
        probabilidade_falso_negativo=0.0,
    )

    sem_ruido = gerar(
        "baseline",
        sem_falso_positivo,
        seed=777,
        quantidade=200,
    )
    com_ruido = gerar(
        "baseline",
        falso_positivo_total,
        seed=777,
        quantidade=200,
    )

    assert [registro.observables for registro in sem_ruido] == [
        registro.observables for registro in com_ruido
    ]

    assert [registro.truth for registro in sem_ruido] == [
        registro.truth for registro in com_ruido
    ]

    assert [registro.operational_labels for registro in sem_ruido] != [
        registro.operational_labels for registro in com_ruido
    ]


@pytest.mark.parametrize(
    (
        "nome_cenario",
        "politica",
        "status_de_erro",
        "taxa_esperada",
    ),
    [
        (
            "baseline",
            OperationalLabelPolicy(
                probabilidade_falso_positivo=0.20,
                probabilidade_falso_negativo=0.0,
            ),
            "Em Análise",
            0.20,
        ),
        (
            "credential_attack",
            OperationalLabelPolicy(
                probabilidade_falso_positivo=0.0,
                probabilidade_falso_negativo=0.30,
            ),
            "Concluída",
            0.30,
        ),
    ],
)
def test_label_policy_intermediaria_produz_ruido_operacional(
    nome_cenario,
    politica,
    status_de_erro,
    taxa_esperada,
):
    registros = gerar(
        nome_cenario,
        politica,
        seed=2026,
        quantidade=5000,
    )

    quantidade_erros = sum(
        registro.operational_labels["status_transacao"] == status_de_erro
        for registro in registros
    )
    taxa_observada = quantidade_erros / len(registros)

    assert 0 < quantidade_erros < len(registros)
    assert taxa_observada == pytest.approx(
        taxa_esperada,
        abs=0.05,
    )
