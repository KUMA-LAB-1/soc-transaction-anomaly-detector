from datetime import datetime, timedelta

import pytest

from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.population import (
    CustomerBehaviorProfile,
    CustomerPopulation,
)
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


def test_gerador_com_populacao_usa_pseudonimo_do_profile():
    population = criar_populacao(
        "entidade-sintetica-alpha",
    )

    gerador = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    )

    registros = gerador.gerar_registros(
        obter_cenario("baseline"),
        quantidade=20,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    assert {registro.observables["cliente_pseudonimo"] for registro in registros} == {
        "entidade-sintetica-alpha",
    }


def test_gerador_rejeita_population_invalida():
    with pytest.raises(
        ValueError,
        match="population",
    ):
        StatisticalGenerator(
            seed=42,
            label_policy=POLITICA_SEM_RUIDO,
            population="population-invalida",
        )


def test_mudar_apenas_identidade_da_populacao_nao_altera_evento():
    population_alpha = criar_populacao(
        "entidade-alpha",
    )
    population_beta = criar_populacao(
        "entidade-beta",
    )

    registros_alpha = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_alpha,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_beta = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_beta,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    observaveis_alpha = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "cliente_pseudonimo"
        }
        for registro in registros_alpha
    ]

    observaveis_beta = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "cliente_pseudonimo"
        }
        for registro in registros_beta
    ]

    assert observaveis_alpha == observaveis_beta

    assert [registro.operational_labels for registro in registros_alpha] == [
        registro.operational_labels for registro in registros_beta
    ]

    assert [registro.truth for registro in registros_alpha] == [
        registro.truth for registro in registros_beta
    ]


def test_profile_controla_mediana_do_valor_transacional():
    population_baixa = criar_populacao(
        "entidade-alpha",
        transaction_value_median=90.0,
        transaction_value_sigma=0.65,
    )
    population_alta = criar_populacao(
        "entidade-alpha",
        transaction_value_median=900.0,
        transaction_value_sigma=0.65,
    )

    registros_baixos = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_baixa,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_altos = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_alta,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    valores_baixos = [
        registro.observables["valor_transacao"] for registro in registros_baixos
    ]
    valores_altos = [
        registro.observables["valor_transacao"] for registro in registros_altos
    ]

    assert valores_baixos != valores_altos
    assert all(
        valor_alto > valor_baixo
        for valor_baixo, valor_alto in zip(
            valores_baixos,
            valores_altos,
            strict=True,
        )
    )


def test_profile_controla_dispersao_do_valor_transacional():
    population_estavel = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.10,
    )
    population_volatil = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=1.20,
    )

    registros_estaveis = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_estavel,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_volateis = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_volatil,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    valores_estaveis = [
        registro.observables["valor_transacao"] for registro in registros_estaveis
    ]
    valores_volateis = [
        registro.observables["valor_transacao"] for registro in registros_volateis
    ]

    assert valores_estaveis != valores_volateis


def test_mudar_apenas_baseline_transacional_nao_embaralha_evento():
    population_baixa = criar_populacao(
        "entidade-alpha",
        transaction_value_median=90.0,
        transaction_value_sigma=0.65,
    )
    population_alta = criar_populacao(
        "entidade-alpha",
        transaction_value_median=900.0,
        transaction_value_sigma=0.65,
    )

    registros_baixos = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_baixa,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_altos = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_alta,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    valores_baixos = [
        registro.observables["valor_transacao"] for registro in registros_baixos
    ]
    valores_altos = [
        registro.observables["valor_transacao"] for registro in registros_altos
    ]

    assert valores_baixos != valores_altos

    observaveis_baixos_sem_valor = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in registros_baixos
    ]
    observaveis_altos_sem_valor = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in registros_altos
    ]

    assert observaveis_baixos_sem_valor == observaveis_altos_sem_valor

    assert [registro.operational_labels for registro in registros_baixos] == [
        registro.operational_labels for registro in registros_altos
    ]

    assert [registro.truth for registro in registros_baixos] == [
        registro.truth for registro in registros_altos
    ]


def test_profile_behavior_flag_baseline_controla_observaveis_booleanos():
    from dataclasses import replace

    from src.synthetic.behavior_flags import BehaviorFlagBaseline

    population = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="entidade-alpha",
                transaction_value_median=180.0,
                transaction_value_sigma=0.65,
                recent_login_failure_rate=0.15,
                behavior_flag_baseline=BehaviorFlagBaseline(
                    new_device_probability=0.0,
                    limit_change_probability=0.0,
                    location_change_probability=0.0,
                ),
            ),
        )
    )

    cenario = replace(
        obter_cenario("baseline"),
        probabilidade_dispositivo_novo=1.0,
        probabilidade_alteracao_limite=1.0,
        probabilidade_mudanca_localizacao=1.0,
    )

    registros = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        cenario,
        quantidade=10,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    assert all(
        registro.observables["dispositivo_novo_flag"] is False for registro in registros
    )
    assert all(
        registro.observables["alteracao_limite_flag"] is False for registro in registros
    )
    assert all(
        registro.observables["mudanca_localizacao_flag"] is False
        for registro in registros
    )


def test_behavior_flag_baseline_equivalente_reproduz_fallback_legado():
    from src.synthetic.behavior_flags import BehaviorFlagBaseline

    cenario = obter_cenario("baseline")

    population_fallback = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="entidade-alpha",
                transaction_value_median=180.0,
                transaction_value_sigma=0.65,
                recent_login_failure_rate=0.15,
            ),
        )
    )

    population_explicit = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="entidade-alpha",
                transaction_value_median=180.0,
                transaction_value_sigma=0.65,
                recent_login_failure_rate=0.15,
                behavior_flag_baseline=BehaviorFlagBaseline(
                    new_device_probability=(cenario.probabilidade_dispositivo_novo),
                    limit_change_probability=(cenario.probabilidade_alteracao_limite),
                    location_change_probability=(
                        cenario.probabilidade_mudanca_localizacao
                    ),
                ),
            ),
        )
    )

    registros_fallback = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_fallback,
    ).gerar_registros(
        cenario,
        quantidade=100,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_explicit = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_explicit,
    ).gerar_registros(
        cenario,
        quantidade=100,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    assert registros_explicit == registros_fallback


def test_mudar_apenas_behavior_flag_baseline_nao_embaralha_restante_do_evento():
    from src.synthetic.behavior_flags import BehaviorFlagBaseline

    population_zero = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="entidade-alpha",
                transaction_value_median=180.0,
                transaction_value_sigma=0.65,
                recent_login_failure_rate=0.15,
                behavior_flag_baseline=BehaviorFlagBaseline(
                    new_device_probability=0.0,
                    limit_change_probability=0.0,
                    location_change_probability=0.0,
                ),
            ),
        )
    )

    population_um = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="entidade-alpha",
                transaction_value_median=180.0,
                transaction_value_sigma=0.65,
                recent_login_failure_rate=0.15,
                behavior_flag_baseline=BehaviorFlagBaseline(
                    new_device_probability=1.0,
                    limit_change_probability=1.0,
                    location_change_probability=1.0,
                ),
            ),
        )
    )

    registros_zero = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_zero,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_um = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_um,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    boolean_fields = {
        "dispositivo_novo_flag",
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    }

    observaveis_zero_sem_flags = [
        {
            field_name: value
            for field_name, value in registro.observables.items()
            if field_name not in boolean_fields
        }
        for registro in registros_zero
    ]

    observaveis_um_sem_flags = [
        {
            field_name: value
            for field_name, value in registro.observables.items()
            if field_name not in boolean_fields
        }
        for registro in registros_um
    ]

    assert observaveis_zero_sem_flags == observaveis_um_sem_flags

    assert [registro.operational_labels for registro in registros_zero] == [
        registro.operational_labels for registro in registros_um
    ]

    assert [registro.truth for registro in registros_zero] == [
        registro.truth for registro in registros_um
    ]

    assert all(
        registro.observables["dispositivo_novo_flag"] is False
        for registro in registros_zero
    )
    assert all(
        registro.observables["alteracao_limite_flag"] is False
        for registro in registros_zero
    )
    assert all(
        registro.observables["mudanca_localizacao_flag"] is False
        for registro in registros_zero
    )

    assert all(
        registro.observables["dispositivo_novo_flag"] is True
        for registro in registros_um
    )
    assert all(
        registro.observables["alteracao_limite_flag"] is True
        for registro in registros_um
    )
    assert all(
        registro.observables["mudanca_localizacao_flag"] is True
        for registro in registros_um
    )


def test_profile_controla_baseline_de_falhas_login():
    population_sem_falhas = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.0,
    )
    population_com_falhas = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=5.0,
    )

    registros_sem_falhas = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_sem_falhas,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_com_falhas = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_com_falhas,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    falhas_sem_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in registros_sem_falhas
    ]
    falhas_com_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in registros_com_falhas
    ]

    assert all(falhas == 0 for falhas in falhas_sem_baseline)
    assert sum(falhas_com_baseline) > 0
    assert falhas_sem_baseline != falhas_com_baseline


def test_mudar_apenas_baseline_login_nao_embaralha_evento():
    population_sem_falhas = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.0,
    )
    population_com_falhas = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=5.0,
    )

    registros_sem_falhas = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_sem_falhas,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_com_falhas = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_com_falhas,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    falhas_sem_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in registros_sem_falhas
    ]
    falhas_com_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in registros_com_falhas
    ]

    assert falhas_sem_baseline != falhas_com_baseline

    observaveis_sem_falhas_login = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "falhas_login_recentes"
        }
        for registro in registros_sem_falhas
    ]
    observaveis_com_falhas_login = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "falhas_login_recentes"
        }
        for registro in registros_com_falhas
    ]

    assert observaveis_sem_falhas_login == observaveis_com_falhas_login

    assert [registro.operational_labels for registro in registros_sem_falhas] == [
        registro.operational_labels for registro in registros_com_falhas
    ]

    assert [registro.truth for registro in registros_sem_falhas] == [
        registro.truth for registro in registros_com_falhas
    ]
