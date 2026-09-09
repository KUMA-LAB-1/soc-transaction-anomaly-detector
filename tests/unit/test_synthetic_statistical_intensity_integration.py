from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from src.synthetic.intensity import EventIntensityPolicy
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.population import CustomerBehaviorProfile, CustomerPopulation
from src.synthetic.scenarios import obter_cenario
from src.synthetic.severity import SeverityPolicy
from src.synthetic.statistical import StatisticalGenerator

INICIO = datetime(2026, 1, 1, 0, 0)
FIM = INICIO + timedelta(days=7)

POLITICA_SEM_RUIDO = OperationalLabelPolicy(
    probabilidade_falso_positivo=0.0,
    probabilidade_falso_negativo=0.0,
)

INTENSITY_POLICY = EventIntensityPolicy(
    intensity_min=0.20,
    intensity_max=0.80,
)


def test_integrar_intensity_policy_preserva_evento_existente():
    sem_intensity = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM,
    )

    com_intensity = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=INTENSITY_POLICY,
    )

    assert [registro.observables for registro in com_intensity] == [
        registro.observables for registro in sem_intensity
    ]

    assert [registro.operational_labels for registro in com_intensity] == [
        registro.operational_labels for registro in sem_intensity
    ]

    assert all(registro.truth.event_intensity is None for registro in sem_intensity)

    assert all(registro.truth.event_intensity is not None for registro in com_intensity)

    truth_sem_intensity = [
        replace(
            registro.truth,
            event_intensity=None,
        )
        for registro in com_intensity
    ]

    assert truth_sem_intensity == [registro.truth for registro in sem_intensity]


def test_mesma_seed_reproduz_mesmas_event_intensities():
    primeira_execucao = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=INTENSITY_POLICY,
    )

    segunda_execucao = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=INTENSITY_POLICY,
    )

    intensidades_primeira = [
        registro.truth.event_intensity for registro in primeira_execucao
    ]
    intensidades_segunda = [
        registro.truth.event_intensity for registro in segunda_execucao
    ]

    assert intensidades_primeira == intensidades_segunda


def test_intensity_policy_preserva_sequencia_de_severity():
    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    sem_intensity = StatisticalGenerator(
        seed=314,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    com_intensity = StatisticalGenerator(
        seed=314,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=INTENSITY_POLICY,
    )

    scores_sem_intensity = [registro.truth.severity_score for registro in sem_intensity]
    scores_com_intensity = [registro.truth.severity_score for registro in com_intensity]

    assert scores_com_intensity == scores_sem_intensity

    assert all(registro.truth.event_intensity is None for registro in sem_intensity)

    assert all(registro.truth.event_intensity is not None for registro in com_intensity)


def test_severity_policy_preserva_sequencia_de_event_intensity():
    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    sem_severity = StatisticalGenerator(
        seed=2718,
        label_policy=POLITICA_SEM_RUIDO,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=INTENSITY_POLICY,
    )

    com_severity = StatisticalGenerator(
        seed=2718,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=INTENSITY_POLICY,
    )

    intensidades_sem_severity = [
        registro.truth.event_intensity for registro in sem_severity
    ]
    intensidades_com_severity = [
        registro.truth.event_intensity for registro in com_severity
    ]

    assert intensidades_com_severity == intensidades_sem_severity

    assert all(registro.truth.severity_score is None for registro in sem_severity)

    assert all(registro.truth.severity_score is not None for registro in com_severity)


def test_integrar_intensity_policy_preserva_evento_com_populacao():
    population = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="cliente-alpha",
                transaction_value_median=90.0,
                transaction_value_sigma=0.40,
                recent_login_failure_rate=0.20,
            ),
            CustomerBehaviorProfile(
                customer_pseudonym="cliente-beta",
                transaction_value_median=350.0,
                transaction_value_sigma=0.65,
                recent_login_failure_rate=1.50,
            ),
            CustomerBehaviorProfile(
                customer_pseudonym="cliente-gamma",
                transaction_value_median=900.0,
                transaction_value_sigma=0.85,
                recent_login_failure_rate=4.00,
            ),
        ),
    )

    sem_intensity = StatisticalGenerator(
        seed=1618,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    com_intensity = StatisticalGenerator(
        seed=1618,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=INTENSITY_POLICY,
    )

    assert (
        len({registro.observables["cliente_pseudonimo"] for registro in sem_intensity})
        > 1
    )

    assert [registro.observables for registro in com_intensity] == [
        registro.observables for registro in sem_intensity
    ]

    assert [registro.operational_labels for registro in com_intensity] == [
        registro.operational_labels for registro in sem_intensity
    ]

    truth_sem_intensity = [
        replace(
            registro.truth,
            event_intensity=None,
        )
        for registro in com_intensity
    ]

    assert truth_sem_intensity == [registro.truth for registro in sem_intensity]


def test_gerador_rejeita_intensity_policy_invalida():
    with pytest.raises(
        ValueError,
        match="intensity_policy",
    ):
        StatisticalGenerator(
            seed=42,
            label_policy=POLITICA_SEM_RUIDO,
        ).gerar_registros(
            obter_cenario("baseline"),
            quantidade=1,
            inicio=INICIO,
            fim=FIM,
            intensity_policy="policy-invalida",
        )
