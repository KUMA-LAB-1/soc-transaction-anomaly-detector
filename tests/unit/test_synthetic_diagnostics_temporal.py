from dataclasses import replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import (
    TemporalDiagnostics,
    analyze_synthetic_dataset,
    analyze_temporal_distribution,
)
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario


def test_analyze_temporal_distribution_calcula_extremos_e_madrugada():
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

    timestamps_controlados = (
        datetime(2026, 1, 1, 1, 0),
        datetime(2026, 1, 1, 5, 59),
        datetime(2026, 1, 1, 6, 0),
        datetime(2026, 1, 1, 18, 30),
    )

    registros_controlados = tuple(
        replace(
            registro,
            observables={
                **registro.observables,
                "data_hora_transacao": timestamp,
            },
        )
        for registro, timestamp in zip(
            dataset.records,
            timestamps_controlados,
            strict=True,
        )
    )

    dataset_controlado = replace(
        dataset,
        records=registros_controlados,
    )

    diagnostics = analyze_temporal_distribution(dataset_controlado)

    assert diagnostics == TemporalDiagnostics(
        earliest_timestamp=datetime(2026, 1, 1, 1, 0),
        latest_timestamp=datetime(2026, 1, 1, 18, 30),
        madrugada_count=2,
        madrugada_proportion=0.5,
    )


def test_analyze_temporal_distribution_rejeita_timestamp_ausente():
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

    observables_sem_timestamp = {
        chave: valor
        for chave, valor in dataset.records[0].observables.items()
        if chave != "data_hora_transacao"
    }

    registro_corrompido = replace(
        dataset.records[0],
        observables=observables_sem_timestamp,
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="observables deve conter data_hora_transacao",
    ):
        analyze_temporal_distribution(dataset_corrompido)


def test_analyze_temporal_distribution_rejeita_timestamp_nao_datetime():
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
            "data_hora_transacao": "2026-01-01 05:00:00",
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="data_hora_transacao deve ser datetime",
    ):
        analyze_temporal_distribution(dataset_corrompido)


def test_analyze_synthetic_dataset_rejeita_timestamp_anterior_ao_manifesto():
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
            "data_hora_transacao": datetime(
                2025,
                12,
                31,
                23,
                59,
                59,
                999999,
            ),
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="timestamps observados devem permanecer dentro da janela do manifesto",
    ):
        analyze_synthetic_dataset(dataset_corrompido)


def test_analyze_synthetic_dataset_rejeita_timestamp_igual_ao_fim_do_manifesto():
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
            "data_hora_transacao": fim,
        },
    )

    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="timestamps observados devem permanecer dentro da janela do manifesto",
    ):
        analyze_synthetic_dataset(dataset_corrompido)


def test_analyze_synthetic_dataset_aceita_timestamp_igual_ao_inicio_do_manifesto():
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

    registro_controlado = replace(
        dataset.records[0],
        observables={
            **dataset.records[0].observables,
            "data_hora_transacao": inicio,
        },
    )

    dataset_controlado = replace(
        dataset,
        records=(registro_controlado,),
    )

    diagnostics = analyze_synthetic_dataset(dataset_controlado)

    assert diagnostics.temporal == TemporalDiagnostics(
        earliest_timestamp=inicio,
        latest_timestamp=inicio,
        madrugada_count=1,
        madrugada_proportion=1.0,
    )
