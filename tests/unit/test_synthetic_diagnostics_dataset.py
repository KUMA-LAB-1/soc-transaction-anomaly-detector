from dataclasses import FrozenInstanceError, replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import (
    DatasetDiagnostics,
    OperationalLabelDiagnostics,
    ScenarioDiagnosticsEntry,
    TemporalDiagnostics,
    analyze_synthetic_dataset,
)
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario


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
        operational_labels=OperationalLabelDiagnostics(
            true_positive=0,
            true_negative=1,
            false_positive=0,
            false_negative=0,
        ),
        temporal=TemporalDiagnostics(
            earliest_timestamp=datetime(2026, 1, 1, 1, 0),
            latest_timestamp=datetime(2026, 1, 1, 1, 0),
            madrugada_count=1,
            madrugada_proportion=1.0,
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
            operational_labels=OperationalLabelDiagnostics(
                true_positive=0,
                true_negative=10,
                false_positive=0,
                false_negative=0,
            ),
            temporal=TemporalDiagnostics(
                earliest_timestamp=datetime(2026, 1, 1, 1, 0),
                latest_timestamp=datetime(2026, 1, 1, 18, 0),
                madrugada_count=1,
                madrugada_proportion=0.1,
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
            operational_labels=OperationalLabelDiagnostics(
                true_positive=0,
                true_negative=10,
                false_positive=0,
                false_negative=0,
            ),
            temporal=TemporalDiagnostics(
                earliest_timestamp=datetime(2026, 1, 1, 1, 0),
                latest_timestamp=datetime(2026, 1, 1, 18, 0),
                madrugada_count=1,
                madrugada_proportion=0.1,
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
            operational_labels=OperationalLabelDiagnostics(
                true_positive=0,
                true_negative=1,
                false_positive=0,
                false_negative=0,
            ),
            temporal=TemporalDiagnostics(
                earliest_timestamp=datetime(2026, 1, 1, 1, 0),
                latest_timestamp=datetime(2026, 1, 1, 1, 0),
                madrugada_count=1,
                madrugada_proportion=1.0,
            ),
        )


def test_analyze_synthetic_dataset_inclui_diagnostico_operacional():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    dataset = generate_synthetic_dataset(
        seed=42,
        quantidade=4,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.50,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=0.50,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
    )

    diagnostics = analyze_synthetic_dataset(dataset)

    assert diagnostics.operational_labels == OperationalLabelDiagnostics(
        true_positive=2,
        true_negative=2,
        false_positive=0,
        false_negative=0,
    )
    assert diagnostics.operational_labels.total_classified == 4
    assert diagnostics.operational_labels.total_classified == diagnostics.total_records


def test_dataset_diagnostics_rejeita_total_operacional_inconsistente():
    with pytest.raises(
        ValueError,
        match="total_classified deve ser igual a total_records",
    ):
        DatasetDiagnostics(
            total_records=10,
            scenarios=(
                ScenarioDiagnosticsEntry(
                    scenario="baseline",
                    observed_count=10,
                    observed_proportion=1.0,
                ),
            ),
            operational_labels=OperationalLabelDiagnostics(
                true_positive=2,
                true_negative=2,
                false_positive=1,
                false_negative=1,
            ),
            temporal=TemporalDiagnostics(
                earliest_timestamp=datetime(2026, 1, 1, 1, 0),
                latest_timestamp=datetime(2026, 1, 1, 18, 0),
                madrugada_count=1,
                madrugada_proportion=0.1,
            ),
        )


def test_dataset_diagnostics_exige_diagnostico_operacional():
    with pytest.raises(
        TypeError,
        match="operational_labels",
    ):
        DatasetDiagnostics(
            total_records=1,
            scenarios=(
                ScenarioDiagnosticsEntry(
                    scenario="baseline",
                    observed_count=1,
                    observed_proportion=1.0,
                ),
            ),
            temporal=TemporalDiagnostics(
                earliest_timestamp=datetime(2026, 1, 1, 1, 0),
                latest_timestamp=datetime(2026, 1, 1, 1, 0),
                madrugada_count=1,
                madrugada_proportion=1.0,
            ),
        )


def test_analyze_synthetic_dataset_inclui_diagnostico_temporal():
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

    diagnostics = analyze_synthetic_dataset(dataset_controlado)

    assert diagnostics.temporal == TemporalDiagnostics(
        earliest_timestamp=datetime(2026, 1, 1, 1, 0),
        latest_timestamp=datetime(2026, 1, 1, 18, 30),
        madrugada_count=2,
        madrugada_proportion=0.5,
    )
