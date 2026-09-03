from dataclasses import FrozenInstanceError, replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import (
    DatasetDiagnostics,
    OperationalLabelDiagnostics,
    ScenarioDiagnosticsEntry,
    analyze_operational_label_confusion,
    analyze_synthetic_dataset,
)
from src.synthetic.label_policy import (
    STATUS_NORMAL,
    STATUS_SUSPEITO,
    OperationalLabelPolicy,
)
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
        operational_labels=OperationalLabelDiagnostics(
            true_positive=0,
            true_negative=1,
            false_positive=0,
            false_negative=0,
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


def test_analyze_operational_label_confusion_conta_tp_tn_fp_fn():
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

    registros_suspeitos = [
        registro for registro in dataset.records if registro.truth.is_suspicious
    ]
    registros_normais = [
        registro for registro in dataset.records if not registro.truth.is_suspicious
    ]

    assert len(registros_suspeitos) == 2
    assert len(registros_normais) == 2

    registros_controlados = (
        replace(
            registros_suspeitos[0],
            operational_labels={"status_transacao": STATUS_SUSPEITO},
        ),
        replace(
            registros_suspeitos[1],
            operational_labels={"status_transacao": STATUS_NORMAL},
        ),
        replace(
            registros_normais[0],
            operational_labels={"status_transacao": STATUS_SUSPEITO},
        ),
        replace(
            registros_normais[1],
            operational_labels={"status_transacao": STATUS_NORMAL},
        ),
    )

    dataset_controlado = replace(
        dataset,
        records=registros_controlados,
    )

    diagnostics = analyze_operational_label_confusion(dataset_controlado)

    assert diagnostics == OperationalLabelDiagnostics(
        true_positive=1,
        true_negative=1,
        false_positive=1,
        false_negative=1,
    )


def test_operational_label_diagnostics_calcula_taxas_observadas():
    diagnostics = OperationalLabelDiagnostics(
        true_positive=7,
        true_negative=18,
        false_positive=2,
        false_negative=3,
    )

    assert diagnostics.false_positive_rate == pytest.approx(0.10)
    assert diagnostics.false_negative_rate == pytest.approx(0.30)


def test_operational_label_diagnostics_fpr_e_none_sem_negativos_reais():
    diagnostics = OperationalLabelDiagnostics(
        true_positive=10,
        true_negative=0,
        false_positive=0,
        false_negative=0,
    )

    assert diagnostics.false_positive_rate is None
    assert diagnostics.false_negative_rate == pytest.approx(0.0)


def test_operational_label_diagnostics_fnr_e_none_sem_positivos_reais():
    diagnostics = OperationalLabelDiagnostics(
        true_positive=0,
        true_negative=10,
        false_positive=0,
        false_negative=0,
    )

    assert diagnostics.false_positive_rate == pytest.approx(0.0)
    assert diagnostics.false_negative_rate is None


def test_analyze_operational_label_confusion_rejeita_status_desconhecido():
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

    registro_corrompido = replace(
        dataset.records[0],
        operational_labels={
            "status_transacao": "Kraken Approved",
        },
    )
    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="status_transacao operacional desconhecido: Kraken Approved",
    ):
        analyze_operational_label_confusion(dataset_corrompido)


def test_analyze_operational_label_confusion_rejeita_status_ausente():
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

    registro_corrompido = replace(
        dataset.records[0],
        operational_labels={},
    )
    dataset_corrompido = replace(
        dataset,
        records=(registro_corrompido,),
    )

    with pytest.raises(
        ValueError,
        match="operational_labels deve conter status_transacao",
    ):
        analyze_operational_label_confusion(dataset_corrompido)


def test_operational_label_diagnostics_rejeita_contagem_negativa():
    with pytest.raises(
        ValueError,
        match="contagens devem ser maiores ou iguais a zero",
    ):
        OperationalLabelDiagnostics(
            true_positive=-1,
            true_negative=1,
            false_positive=0,
            false_negative=0,
        )


def test_operational_label_diagnostics_rejeita_contagem_nao_inteira():
    with pytest.raises(
        TypeError,
        match="contagens devem ser inteiros",
    ):
        OperationalLabelDiagnostics(
            true_positive=1.5,
            true_negative=1,
            false_positive=0,
            false_negative=0,
        )


def test_operational_label_diagnostics_rejeita_bool_como_contagem():
    with pytest.raises(
        TypeError,
        match="contagens devem ser inteiros",
    ):
        OperationalLabelDiagnostics(
            true_positive=True,
            true_negative=1,
            false_positive=0,
            false_negative=0,
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
        )
