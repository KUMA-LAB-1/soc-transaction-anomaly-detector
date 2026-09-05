from dataclasses import replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import (
    DatasetDiagnostics,
    OperationalLabelDiagnostics,
    ScenarioDiagnosticsEntry,
    analyze_synthetic_dataset,
    analyze_temporal_distribution,
)
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario


def test_analyze_synthetic_dataset_calcula_distribuicao_observada_dos_cenarios():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.70,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=0.20,
            ),
            ScenarioMix(
                cenario=obter_cenario("account_takeover"),
                proporcao=0.10,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
    )

    diagnostics = analyze_synthetic_dataset(dataset)

    assert diagnostics == DatasetDiagnostics(
        total_records=10,
        scenarios=(
            ScenarioDiagnosticsEntry(
                scenario="baseline",
                observed_count=7,
                observed_proportion=0.70,
            ),
            ScenarioDiagnosticsEntry(
                scenario="credential_attack",
                observed_count=2,
                observed_proportion=0.20,
            ),
            ScenarioDiagnosticsEntry(
                scenario="account_takeover",
                observed_count=1,
                observed_proportion=0.10,
            ),
        ),
        operational_labels=OperationalLabelDiagnostics(
            true_positive=3,
            true_negative=7,
            false_positive=0,
            false_negative=0,
        ),
        temporal=analyze_temporal_distribution(dataset),
    )


def test_analyze_synthetic_dataset_preserva_cenario_sem_registros_observados():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=1,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.99,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=0.01,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
    )

    diagnostics = analyze_synthetic_dataset(dataset)

    assert diagnostics.scenarios == (
        ScenarioDiagnosticsEntry(
            scenario="baseline",
            observed_count=1,
            observed_proportion=1.0,
        ),
        ScenarioDiagnosticsEntry(
            scenario="credential_attack",
            observed_count=0,
            observed_proportion=0.0,
        ),
    )


def test_analyze_synthetic_dataset_rejeita_cenario_observado_ausente_do_manifesto():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

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

    truth_corrompido = replace(
        dataset.records[0].truth,
        scenario="alien_scenario",
    )
    registro_corrompido = replace(
        dataset.records[0],
        truth=truth_corrompido,
    )
    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="cenários observados ausentes do manifesto: alien_scenario",
    ):
        analyze_synthetic_dataset(dataset_corrompido)


def test_analyze_synthetic_dataset_ordena_cenarios_desconhecidos_no_erro():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

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

    cenarios_corrompidos = (
        "zombie_scenario",
        "alien_scenario",
        "kraken_scenario",
    )

    registros_corrompidos = tuple(
        replace(
            registro,
            truth=replace(
                registro.truth,
                scenario=cenario,
            ),
        )
        for registro, cenario in zip(
            dataset.records,
            cenarios_corrompidos,
            strict=True,
        )
    )

    dataset_corrompido = replace(
        dataset,
        records=registros_corrompidos,
    )

    with pytest.raises(
        ValueError,
        match=(
            "cenários observados ausentes do manifesto: "
            "alien_scenario, kraken_scenario, zombie_scenario"
        ),
    ):
        analyze_synthetic_dataset(dataset_corrompido)


def test_analyze_synthetic_dataset_agrega_cenarios_repetidos_do_manifesto():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.40,
            ),
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.60,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
    )

    diagnostics = analyze_synthetic_dataset(dataset)

    assert diagnostics.scenarios == (
        ScenarioDiagnosticsEntry(
            scenario="baseline",
            observed_count=10,
            observed_proportion=1.0,
        ),
    )
