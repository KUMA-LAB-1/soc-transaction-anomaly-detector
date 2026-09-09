from dataclasses import replace
from datetime import datetime, timedelta

import pytest

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

SEVERITY_POLICY = SeverityPolicy(
    normal_min=0.0,
    normal_max=40.0,
    suspicious_min=20.0,
    suspicious_max=100.0,
)


def test_integrar_severity_policy_preserva_evento_existente():
    sem_severity = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM,
    )

    com_severity = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=SEVERITY_POLICY,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM,
    )

    assert [registro.observables for registro in com_severity] == [
        registro.observables for registro in sem_severity
    ]

    assert [registro.operational_labels for registro in com_severity] == [
        registro.operational_labels for registro in sem_severity
    ]

    assert all(registro.truth.severity_score is None for registro in sem_severity)

    assert all(registro.truth.severity_score is not None for registro in com_severity)

    truth_sem_severity = [
        replace(
            registro.truth,
            severity_score=None,
        )
        for registro in com_severity
    ]

    assert truth_sem_severity == [registro.truth for registro in sem_severity]


def test_mesma_seed_reproduz_mesmos_severity_scores():
    primeira_execucao = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=SEVERITY_POLICY,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    segunda_execucao = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=SEVERITY_POLICY,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    scores_primeira = [registro.truth.severity_score for registro in primeira_execucao]
    scores_segunda = [registro.truth.severity_score for registro in segunda_execucao]

    assert scores_primeira == scores_segunda


def test_gerador_rejeita_severity_policy_invalida():
    with pytest.raises(
        ValueError,
        match="severity_policy",
    ):
        StatisticalGenerator(
            seed=42,
            label_policy=POLITICA_SEM_RUIDO,
            severity_policy="policy-invalida",
        )


def test_integrar_severity_policy_preserva_evento_com_populacao():
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

    sem_severity = StatisticalGenerator(
        seed=314,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    com_severity = StatisticalGenerator(
        seed=314,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
        severity_policy=SEVERITY_POLICY,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    assert (
        len({registro.observables["cliente_pseudonimo"] for registro in sem_severity})
        > 1
    )

    assert [registro.observables for registro in com_severity] == [
        registro.observables for registro in sem_severity
    ]

    assert [registro.operational_labels for registro in com_severity] == [
        registro.operational_labels for registro in sem_severity
    ]

    truth_sem_severity = [
        replace(
            registro.truth,
            severity_score=None,
        )
        for registro in com_severity
    ]

    assert truth_sem_severity == [registro.truth for registro in sem_severity]


def test_cenario_seleciona_faixa_correta_de_severity():
    policy = SeverityPolicy(
        normal_min=12.0,
        normal_max=12.0,
        suspicious_min=88.0,
        suspicious_max=88.0,
    )

    baseline = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=policy,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=10,
        inicio=INICIO,
        fim=FIM,
    )

    credential_attack = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=policy,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=10,
        inicio=INICIO,
        fim=FIM,
    )

    assert {registro.truth.severity_score for registro in baseline} == {12.0}

    assert {registro.truth.severity_score for registro in credential_attack} == {88.0}
