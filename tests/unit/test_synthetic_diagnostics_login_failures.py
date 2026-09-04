from dataclasses import replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import analyze_scenario_observables
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario


def test_analyze_scenario_observables_calcula_media_de_falhas_login():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 2, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=4,
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

    falhas_controladas = (
        0,
        1,
        2,
        3,
    )

    registros_controlados = tuple(
        replace(
            registro,
            observables={
                **registro.observables,
                "falhas_login_recentes": falhas,
            },
        )
        for registro, falhas in zip(
            dataset.records,
            falhas_controladas,
            strict=True,
        )
    )

    dataset_controlado = replace(
        dataset,
        records=registros_controlados,
    )

    diagnostics = analyze_scenario_observables(dataset_controlado)

    assert diagnostics[0].recent_login_failures_mean == 1.5


def test_analyze_scenario_observables_rejeita_falhas_login_recentes_ausente():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 2, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=1,
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

    observables_sem_falhas = {
        chave: valor
        for chave, valor in dataset.records[0].observables.items()
        if chave != "falhas_login_recentes"
    }

    registro_corrompido = replace(
        dataset.records[0],
        observables=observables_sem_falhas,
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="observables deve conter falhas_login_recentes",
    ):
        analyze_scenario_observables(dataset_corrompido)


def test_analyze_scenario_observables_rejeita_falhas_login_recentes_nao_inteiro():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 2, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=1,
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

    registro_corrompido = replace(
        dataset.records[0],
        observables={
            **dataset.records[0].observables,
            "falhas_login_recentes": 1.5,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="falhas_login_recentes deve ser inteiro",
    ):
        analyze_scenario_observables(dataset_corrompido)


def test_analyze_scenario_observables_rejeita_falhas_login_recentes_booleano():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 2, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=1,
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

    registro_corrompido = replace(
        dataset.records[0],
        observables={
            **dataset.records[0].observables,
            "falhas_login_recentes": True,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="falhas_login_recentes deve ser inteiro",
    ):
        analyze_scenario_observables(dataset_corrompido)


def test_analyze_scenario_observables_rejeita_falhas_login_recentes_negativo():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 2, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=1,
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

    registro_corrompido = replace(
        dataset.records[0],
        observables={
            **dataset.records[0].observables,
            "falhas_login_recentes": -1,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="falhas_login_recentes deve ser maior ou igual a zero",
    ):
        analyze_scenario_observables(dataset_corrompido)
