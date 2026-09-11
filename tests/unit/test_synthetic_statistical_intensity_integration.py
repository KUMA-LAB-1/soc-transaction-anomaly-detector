from dataclasses import replace
from datetime import datetime, timedelta

import pytest

from src.synthetic.intensity import EventIntensityPolicy
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.population import CustomerBehaviorProfile, CustomerPopulation
from src.synthetic.scenario_effects import ScenarioEffect
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


def test_event_intensity_escala_deltas_booleanos_entre_zero_e_um():
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

    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
        new_device_probability_delta=1.0,
        limit_change_probability_delta=1.0,
        location_change_probability_delta=1.0,
    )

    intensity_zero = EventIntensityPolicy(
        intensity_min=0.0,
        intensity_max=0.0,
    )
    intensity_um = EventIntensityPolicy(
        intensity_min=1.0,
        intensity_max=1.0,
    )

    registros_zero = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=10,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=effect,
        intensity_policy=intensity_zero,
    )

    registros_um = StatisticalGenerator(
        seed=2026,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=10,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=effect,
        intensity_policy=intensity_um,
    )

    assert all(registro.truth.event_intensity == 0.0 for registro in registros_zero)
    assert all(registro.truth.event_intensity == 1.0 for registro in registros_um)

    for field_name in (
        "dispositivo_novo_flag",
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    ):
        assert all(
            registro.observables[field_name] is False for registro in registros_zero
        )
        assert all(
            registro.observables[field_name] is True for registro in registros_um
        )


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


def test_intensidade_zero_neutraliza_scenario_effect_transacional():
    population = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="cliente-alpha",
                transaction_value_median=180.0,
                transaction_value_sigma=0.65,
                recent_login_failure_rate=0.15,
            ),
        )
    )

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )

    intensity_zero = EventIntensityPolicy(
        intensity_min=0.0,
        intensity_max=0.0,
    )

    sem_efeito = StatisticalGenerator(
        seed=4242,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("transaction_anomaly"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM,
    )

    efeito_com_intensidade_zero = StatisticalGenerator(
        seed=4242,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("transaction_anomaly"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect,
        intensity_policy=intensity_zero,
    )

    assert [registro.observables for registro in efeito_com_intensidade_zero] == [
        registro.observables for registro in sem_efeito
    ]

    assert {
        registro.truth.event_intensity for registro in efeito_com_intensidade_zero
    } == {0.0}

    assert all(registro.truth.event_intensity is None for registro in sem_efeito)


def test_intensidade_um_preserva_scenario_effect_completo():
    population = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="cliente-alpha",
                transaction_value_median=220.0,
                transaction_value_sigma=0.70,
                recent_login_failure_rate=0.30,
            ),
        )
    )

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.40,
        recent_login_failure_rate_increment=3.0,
    )

    intensity_one = EventIntensityPolicy(
        intensity_min=1.0,
        intensity_max=1.0,
    )

    efeito_legado = StatisticalGenerator(
        seed=5150,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect,
    )

    efeito_com_intensidade_um = StatisticalGenerator(
        seed=5150,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect,
        intensity_policy=intensity_one,
    )

    assert [registro.observables for registro in efeito_com_intensidade_um] == [
        registro.observables for registro in efeito_legado
    ]

    assert [registro.operational_labels for registro in efeito_com_intensidade_um] == [
        registro.operational_labels for registro in efeito_legado
    ]

    assert {
        registro.truth.event_intensity for registro in efeito_com_intensidade_um
    } == {1.0}

    truth_sem_intensity = [
        replace(
            registro.truth,
            event_intensity=None,
        )
        for registro in efeito_com_intensidade_um
    ]

    assert truth_sem_intensity == [registro.truth for registro in efeito_legado]


def test_intensidade_intermediaria_aplica_scenario_effect_intermediario():
    population = CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym="cliente-alpha",
                transaction_value_median=240.0,
                transaction_value_sigma=0.60,
                recent_login_failure_rate=0.40,
            ),
        )
    )

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.40,
        recent_login_failure_rate_increment=3.0,
    )

    scenario_effect_intermediario = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.20,
        recent_login_failure_rate_increment=1.5,
    )

    intensity_half = EventIntensityPolicy(
        intensity_min=0.5,
        intensity_max=0.5,
    )

    referencia = StatisticalGenerator(
        seed=8080,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect_intermediario,
    )

    modulado = StatisticalGenerator(
        seed=8080,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect,
        intensity_policy=intensity_half,
    )

    assert [registro.observables for registro in modulado] == [
        registro.observables for registro in referencia
    ]

    assert [registro.operational_labels for registro in modulado] == [
        registro.operational_labels for registro in referencia
    ]

    assert {registro.truth.event_intensity for registro in modulado} == {0.5}

    truth_sem_intensity = [
        replace(
            registro.truth,
            event_intensity=None,
        )
        for registro in modulado
    ]

    assert truth_sem_intensity == [registro.truth for registro in referencia]


def test_event_intensity_determina_severity_quando_modula_scenario_effect():
    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.40,
        recent_login_failure_rate_increment=3.0,
    )

    intensity_half = EventIntensityPolicy(
        intensity_min=0.5,
        intensity_max=0.5,
    )

    registros = StatisticalGenerator(
        seed=9090,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect,
        intensity_policy=intensity_half,
    )

    assert {registro.truth.event_intensity for registro in registros} == {0.5}

    assert {registro.truth.severity_score for registro in registros} == {60.0}


def test_modo_causal_preserva_estado_futuro_do_severity_rng():
    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.40,
        recent_login_failure_rate_increment=3.0,
    )

    intensity_half = EventIntensityPolicy(
        intensity_min=0.5,
        intensity_max=0.5,
    )

    gerador_causal = StatisticalGenerator(
        seed=12345,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    )

    gerador_referencia = StatisticalGenerator(
        seed=12345,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    )

    gerador_causal.gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=40,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect,
        intensity_policy=intensity_half,
    )

    gerador_referencia.gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=40,
        inicio=INICIO,
        fim=FIM,
    )

    lote_futuro_causal = gerador_causal.gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=30,
        inicio=INICIO,
        fim=FIM,
    )

    lote_futuro_referencia = gerador_referencia.gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=30,
        inicio=INICIO,
        fim=FIM,
    )

    scores_causal = [registro.truth.severity_score for registro in lote_futuro_causal]

    scores_referencia = [
        registro.truth.severity_score for registro in lote_futuro_referencia
    ]

    assert scores_causal == scores_referencia


def test_scenario_effect_sem_intensity_preserva_sequencia_de_severity():
    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.40,
        recent_login_failure_rate_increment=3.0,
    )

    referencia = StatisticalGenerator(
        seed=2468,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    com_scenario_effect = StatisticalGenerator(
        seed=2468,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect,
    )

    scores_referencia = [registro.truth.severity_score for registro in referencia]

    scores_com_scenario_effect = [
        registro.truth.severity_score for registro in com_scenario_effect
    ]

    assert scores_com_scenario_effect == scores_referencia

    assert all(registro.truth.event_intensity is None for registro in referencia)

    assert all(
        registro.truth.event_intensity is None for registro in com_scenario_effect
    )


def test_scenario_effect_neutro_nao_acopla_intensity_a_severity():
    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    scenario_effect_neutro = ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )

    intensity_half = EventIntensityPolicy(
        intensity_min=0.5,
        intensity_max=0.5,
    )

    referencia = StatisticalGenerator(
        seed=8642,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=intensity_half,
    )

    com_efeito_neutro = StatisticalGenerator(
        seed=8642,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect_neutro,
        intensity_policy=intensity_half,
    )

    assert [registro.observables for registro in com_efeito_neutro] == [
        registro.observables for registro in referencia
    ]

    assert [registro.truth.event_intensity for registro in com_efeito_neutro] == [
        registro.truth.event_intensity for registro in referencia
    ]

    scores_referencia = [registro.truth.severity_score for registro in referencia]

    scores_efeito_neutro = [
        registro.truth.severity_score for registro in com_efeito_neutro
    ]

    assert scores_efeito_neutro == scores_referencia


def test_intensidade_zero_que_neutraliza_efeito_nao_acopla_intensity_a_severity():
    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.40,
        recent_login_failure_rate_increment=3.0,
    )

    intensity_zero = EventIntensityPolicy(
        intensity_min=0.0,
        intensity_max=0.0,
    )

    referencia = StatisticalGenerator(
        seed=97531,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        intensity_policy=intensity_zero,
    )

    com_efeito_neutralizado = StatisticalGenerator(
        seed=97531,
        label_policy=POLITICA_SEM_RUIDO,
        severity_policy=severity_policy,
    ).gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
        scenario_effect=scenario_effect,
        intensity_policy=intensity_zero,
    )

    assert [registro.observables for registro in com_efeito_neutralizado] == [
        registro.observables for registro in referencia
    ]

    assert {registro.truth.event_intensity for registro in com_efeito_neutralizado} == {
        0.0
    }

    scores_referencia = [registro.truth.severity_score for registro in referencia]

    scores_efeito_neutralizado = [
        registro.truth.severity_score for registro in com_efeito_neutralizado
    ]

    assert scores_efeito_neutralizado == scores_referencia
