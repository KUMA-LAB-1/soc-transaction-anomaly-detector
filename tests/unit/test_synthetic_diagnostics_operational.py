from dataclasses import replace
from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset
from src.synthetic.diagnostics import (
    OperationalLabelDiagnostics,
    analyze_operational_label_confusion,
)
from src.synthetic.label_policy import (
    STATUS_NORMAL,
    STATUS_SUSPEITO,
    OperationalLabelPolicy,
)
from src.synthetic.scenarios import obter_cenario


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
