from datetime import datetime, timedelta

from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.population import (
    CustomerBehaviorProfile,
    CustomerPopulation,
)
from src.synthetic.scenario_effects import ScenarioEffect
from src.synthetic.scenarios import obter_cenario
from src.synthetic.statistical import StatisticalGenerator

INICIO = datetime(2026, 1, 1, 0, 0)
FIM_PADRAO = INICIO + timedelta(days=30)

POLITICA_SEM_RUIDO = OperationalLabelPolicy(
    probabilidade_falso_positivo=0.0,
    probabilidade_falso_negativo=0.0,
)


def criar_populacao(
    customer_pseudonym: str,
    *,
    transaction_value_median: float = 180.0,
    transaction_value_sigma: float = 0.65,
    recent_login_failure_rate: float = 0.15,
) -> CustomerPopulation:
    return CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym=customer_pseudonym,
                transaction_value_median=transaction_value_median,
                transaction_value_sigma=transaction_value_sigma,
                recent_login_failure_rate=recent_login_failure_rate,
            ),
        )
    )


def test_scenario_effect_neutro_preserva_baseline_transacional():
    population = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.15,
    )

    effect_neutro = ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )

    registros_sem_efeito = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_com_efeito = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
        scenario_effect=effect_neutro,
    )

    assert registros_com_efeito == registros_sem_efeito


def test_scenario_effect_transacional_modifica_apenas_valor_transacao():
    population = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.15,
    )

    effect_transacional = ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )

    registros_sem_efeito = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("transaction_anomaly"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_com_efeito = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("transaction_anomaly"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
        scenario_effect=effect_transacional,
    )

    valores_sem_efeito = [
        registro.observables["valor_transacao"] for registro in registros_sem_efeito
    ]
    valores_com_efeito = [
        registro.observables["valor_transacao"] for registro in registros_com_efeito
    ]

    assert valores_sem_efeito != valores_com_efeito

    assert all(
        valor_com_efeito > valor_sem_efeito
        for valor_sem_efeito, valor_com_efeito in zip(
            valores_sem_efeito,
            valores_com_efeito,
            strict=True,
        )
    )

    observaveis_sem_valor_sem_efeito = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in registros_sem_efeito
    ]
    observaveis_sem_valor_com_efeito = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in registros_com_efeito
    ]

    assert observaveis_sem_valor_com_efeito == observaveis_sem_valor_sem_efeito

    assert [registro.operational_labels for registro in registros_com_efeito] == [
        registro.operational_labels for registro in registros_sem_efeito
    ]

    assert [registro.truth for registro in registros_com_efeito] == [
        registro.truth for registro in registros_sem_efeito
    ]


def test_scenario_effect_controla_dispersao_transacional():
    population = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.15,
    )

    effect_neutro = ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )
    effect_sem_dispersao = ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=0.0,
        recent_login_failure_rate_increment=0.0,
    )

    registros_neutros = StatisticalGenerator(
        seed=314,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
        scenario_effect=effect_neutro,
    )

    registros_sem_dispersao = StatisticalGenerator(
        seed=314,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
        scenario_effect=effect_sem_dispersao,
    )

    valores_neutros = [
        registro.observables["valor_transacao"] for registro in registros_neutros
    ]
    valores_sem_dispersao = [
        registro.observables["valor_transacao"] for registro in registros_sem_dispersao
    ]

    assert valores_neutros != valores_sem_dispersao
    assert all(valor == 180.0 for valor in valores_sem_dispersao)

    observaveis_neutros_sem_valor = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in registros_neutros
    ]
    observaveis_sem_dispersao_sem_valor = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in registros_sem_dispersao
    ]

    assert observaveis_neutros_sem_valor == observaveis_sem_dispersao_sem_valor

    assert [registro.operational_labels for registro in registros_neutros] == [
        registro.operational_labels for registro in registros_sem_dispersao
    ]

    assert [registro.truth for registro in registros_neutros] == [
        registro.truth for registro in registros_sem_dispersao
    ]
