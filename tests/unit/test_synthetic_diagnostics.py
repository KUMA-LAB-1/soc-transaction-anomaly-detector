from dataclasses import FrozenInstanceError, replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import (
    DatasetDiagnostics,
    ScenarioDiagnosticsEntry,
    analyze_synthetic_dataset,
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


def test_dataset_diagnostics_e_estruturalmente_imutavel():
    diagnostics = DatasetDiagnostics(
        total_records=1,
        scenarios=(
            ScenarioDiagnosticsEntry(
                scenario="baseline",
                observed_count=1,
                observed_proportion=1.0,
            ),
        ),
    )

    assert isinstance(diagnostics.scenarios, tuple)

    with pytest.raises(FrozenInstanceError):
        diagnostics.total_records = 2


def test_dataset_diagnostics_rejeita_soma_de_contagens_inconsistente():
    with pytest.raises(
        ValueError,
        match="soma de observed_count deve ser igual a total_records",
    ):
        DatasetDiagnostics(
            total_records=10,
            scenarios=(
                ScenarioDiagnosticsEntry(
                    scenario="baseline",
                    observed_count=7,
                    observed_proportion=0.7,
                ),
                ScenarioDiagnosticsEntry(
                    scenario="credential_attack",
                    observed_count=2,
                    observed_proportion=0.2,
                ),
            ),
        )


def test_dataset_diagnostics_rejeita_proporcao_inconsistente_com_contagem():
    with pytest.raises(
        ValueError,
        match="observed_proportion deve corresponder a observed_count",
    ):
        DatasetDiagnostics(
            total_records=10,
            scenarios=(
                ScenarioDiagnosticsEntry(
                    scenario="baseline",
                    observed_count=7,
                    observed_proportion=0.6,
                ),
                ScenarioDiagnosticsEntry(
                    scenario="credential_attack",
                    observed_count=3,
                    observed_proportion=0.4,
                ),
            ),
        )


def test_dataset_diagnostics_rejeita_scenarios_fora_de_tuple():
    with pytest.raises(
        TypeError,
        match="scenarios deve ser uma tuple",
    ):
        DatasetDiagnostics(
            total_records=1,
            scenarios=[
                ScenarioDiagnosticsEntry(
                    scenario="baseline",
                    observed_count=1,
                    observed_proportion=1.0,
                )
            ],
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
