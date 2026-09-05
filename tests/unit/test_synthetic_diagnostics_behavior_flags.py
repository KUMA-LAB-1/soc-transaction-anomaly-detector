from dataclasses import replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import analyze_scenario_observables
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario


def _generate_baseline_dataset(quantidade: int):
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 2, 0, 0)

    return generate_synthetic_dataset(
        seed=42,
        quantidade=quantidade,
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


def test_analyze_scenario_observables_calcula_proporcao_dispositivo_novo():

    dataset = _generate_baseline_dataset(quantidade=4)

    flags_controladas = (
        True,
        False,
        True,
        False,
    )

    registros_controlados = tuple(
        replace(
            registro,
            observables={
                **registro.observables,
                "dispositivo_novo_flag": flag,
            },
        )
        for registro, flag in zip(
            dataset.records,
            flags_controladas,
            strict=True,
        )
    )

    dataset_controlado = replace(
        dataset,
        records=registros_controlados,
    )

    diagnostics = analyze_scenario_observables(dataset_controlado)

    assert diagnostics[0].new_device_proportion == 0.5


def test_analyze_scenario_observables_rejeita_dispositivo_novo_flag_ausente():

    dataset = _generate_baseline_dataset(quantidade=1)

    observables_sem_flag = {
        chave: valor
        for chave, valor in dataset.records[0].observables.items()
        if chave != "dispositivo_novo_flag"
    }

    registro_corrompido = replace(
        dataset.records[0],
        observables=observables_sem_flag,
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="observables deve conter dispositivo_novo_flag",
    ):
        analyze_scenario_observables(dataset_corrompido)


@pytest.mark.parametrize(
    "valor_invalido",
    [
        1,
        0,
        "true",
        None,
    ],
)
def test_analyze_scenario_observables_rejeita_dispositivo_novo_flag_nao_booleano(
    valor_invalido,
):

    dataset = _generate_baseline_dataset(quantidade=1)

    registro_corrompido = replace(
        dataset.records[0],
        observables={
            **dataset.records[0].observables,
            "dispositivo_novo_flag": valor_invalido,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="dispositivo_novo_flag deve ser booleano",
    ):
        analyze_scenario_observables(dataset_corrompido)


def test_analyze_scenario_observables_calcula_proporcao_alteracao_limite():

    dataset = _generate_baseline_dataset(quantidade=4)

    flags_controladas = (
        True,
        True,
        False,
        False,
    )

    registros_controlados = tuple(
        replace(
            registro,
            observables={
                **registro.observables,
                "alteracao_limite_flag": flag,
            },
        )
        for registro, flag in zip(
            dataset.records,
            flags_controladas,
            strict=True,
        )
    )

    dataset_controlado = replace(
        dataset,
        records=registros_controlados,
    )

    diagnostics = analyze_scenario_observables(dataset_controlado)

    assert diagnostics[0].limit_change_proportion == 0.5


def test_analyze_scenario_observables_rejeita_alteracao_limite_flag_ausente():

    dataset = _generate_baseline_dataset(quantidade=1)

    observables_sem_flag = {
        chave: valor
        for chave, valor in dataset.records[0].observables.items()
        if chave != "alteracao_limite_flag"
    }

    registro_corrompido = replace(
        dataset.records[0],
        observables=observables_sem_flag,
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="observables deve conter alteracao_limite_flag",
    ):
        analyze_scenario_observables(dataset_corrompido)


@pytest.mark.parametrize(
    "valor_invalido",
    [
        1,
        0,
        "true",
        None,
    ],
)
def test_analyze_scenario_observables_rejeita_alteracao_limite_flag_nao_booleano(
    valor_invalido,
):

    dataset = _generate_baseline_dataset(quantidade=1)

    registro_corrompido = replace(
        dataset.records[0],
        observables={
            **dataset.records[0].observables,
            "alteracao_limite_flag": valor_invalido,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="alteracao_limite_flag deve ser booleano",
    ):
        analyze_scenario_observables(dataset_corrompido)


def test_analyze_scenario_observables_calcula_proporcao_mudanca_localizacao():

    dataset = _generate_baseline_dataset(quantidade=4)

    flags_controladas = (
        True,
        False,
        False,
        False,
    )

    registros_controlados = tuple(
        replace(
            registro,
            observables={
                **registro.observables,
                "mudanca_localizacao_flag": flag,
            },
        )
        for registro, flag in zip(
            dataset.records,
            flags_controladas,
            strict=True,
        )
    )

    dataset_controlado = replace(
        dataset,
        records=registros_controlados,
    )

    diagnostics = analyze_scenario_observables(dataset_controlado)

    assert diagnostics[0].location_change_proportion == 0.25


def test_analyze_scenario_observables_rejeita_mudanca_localizacao_flag_ausente():

    dataset = _generate_baseline_dataset(quantidade=1)

    observables_sem_flag = {
        chave: valor
        for chave, valor in dataset.records[0].observables.items()
        if chave != "mudanca_localizacao_flag"
    }

    registro_corrompido = replace(
        dataset.records[0],
        observables=observables_sem_flag,
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="observables deve conter mudanca_localizacao_flag",
    ):
        analyze_scenario_observables(dataset_corrompido)


@pytest.mark.parametrize(
    "valor_invalido",
    [
        1,
        0,
        "true",
        None,
    ],
)
def test_analyze_scenario_observables_rejeita_mudanca_localizacao_flag_nao_booleano(
    valor_invalido,
):

    dataset = _generate_baseline_dataset(quantidade=1)

    registro_corrompido = replace(
        dataset.records[0],
        observables={
            **dataset.records[0].observables,
            "mudanca_localizacao_flag": valor_invalido,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="mudanca_localizacao_flag deve ser booleano",
    ):
        analyze_scenario_observables(dataset_corrompido)
