from dataclasses import replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import analyze_scenario_observables
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario


def test_analyze_scenario_observables_calcula_mediana_do_valor_transacao():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 2, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=3,
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

    valores_controlados = (
        10.0,
        20.0,
        1000.0,
    )

    registros_controlados = tuple(
        replace(
            registro,
            observables={
                **registro.observables,
                "valor_transacao": valor,
            },
        )
        for registro, valor in zip(
            dataset.records,
            valores_controlados,
            strict=True,
        )
    )

    dataset_controlado = replace(
        dataset,
        records=registros_controlados,
    )

    diagnostics = analyze_scenario_observables(dataset_controlado)

    assert len(diagnostics) == 1
    assert diagnostics[0].scenario == "baseline"
    assert diagnostics[0].record_count == 3
    assert diagnostics[0].transaction_value_median == 20.0


def test_analyze_scenario_observables_rejeita_valor_transacao_ausente():
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

    observables_sem_valor = {
        chave: valor
        for chave, valor in dataset.records[0].observables.items()
        if chave != "valor_transacao"
    }

    registro_corrompido = replace(
        dataset.records[0],
        observables=observables_sem_valor,
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="observables deve conter valor_transacao",
    ):
        analyze_scenario_observables(dataset_corrompido)


def test_analyze_scenario_observables_rejeita_valor_transacao_nao_numerico():
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
            "valor_transacao": "Kraken Approved",
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="valor_transacao deve ser numerico",
    ):
        analyze_scenario_observables(dataset_corrompido)


def test_analyze_scenario_observables_rejeita_valor_transacao_booleano():
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
            "valor_transacao": True,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="valor_transacao deve ser numerico",
    ):
        analyze_scenario_observables(dataset_corrompido)


@pytest.mark.parametrize(
    "valor_invalido",
    [
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_analyze_scenario_observables_rejeita_valor_transacao_nao_finito(
    valor_invalido,
):
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
            "valor_transacao": valor_invalido,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="valor_transacao deve ser finito",
    ):
        analyze_scenario_observables(dataset_corrompido)
