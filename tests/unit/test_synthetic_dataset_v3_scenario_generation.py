from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset_v3
from src.synthetic.generation_config import (
    ScenarioGenerationConfig,
    SyntheticGenerationConfig,
)
from src.synthetic.intensity import EventIntensityPolicy
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.population_generation import PopulationGenerationConfig
from src.synthetic.scenario_effects import ScenarioEffect
from src.synthetic.scenarios import obter_cenario


def test_generate_synthetic_dataset_v3_aplica_scenario_effect_com_intensity():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    population_config = PopulationGenerationConfig(
        customer_count=1,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.0,
        transaction_value_sigma=0.10,
        recent_login_failure_rate_mean=0.0,
        recent_login_failure_rate_shape=2.0,
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("transaction_anomaly"),
            proporcao=1.0,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    referencia = generate_synthetic_dataset_v3(
        seed=777,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
        ),
    )

    modulado = generate_synthetic_dataset_v3(
        seed=777,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="transaction_anomaly",
                    scenario_effect=ScenarioEffect(
                        transaction_value_median_multiplier=2.0,
                        transaction_value_sigma_multiplier=1.0,
                        recent_login_failure_rate_increment=0.0,
                    ),
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=1.0,
                        intensity_max=1.0,
                    ),
                ),
            ),
        ),
    )

    valores_referencia = [
        registro.observables["valor_transacao"] for registro in referencia.records
    ]
    valores_modulados = [
        registro.observables["valor_transacao"] for registro in modulado.records
    ]

    assert all(
        valor_modulado > valor_referencia
        for valor_referencia, valor_modulado in zip(
            valores_referencia,
            valores_modulados,
            strict=True,
        )
    )

    assert all(
        registro.truth.event_intensity is None for registro in referencia.records
    )
    assert {registro.truth.event_intensity for registro in modulado.records} == {1.0}

    assert len(modulado.manifest.generation.scenarios) == 1

    scenario_manifest = modulado.manifest.generation.scenarios[0]

    assert scenario_manifest.scenario == "transaction_anomaly"
    assert scenario_manifest.scenario_effect.transaction_value_median_multiplier == 2.0
    assert scenario_manifest.intensity_policy.intensity_min == 1.0
    assert scenario_manifest.intensity_policy.intensity_max == 1.0


def test_generate_synthetic_dataset_v3_rejeita_scenario_effect_sem_population():
    generation_config = SyntheticGenerationConfig(
        scenario_configs=(
            ScenarioGenerationConfig(
                scenario="transaction_anomaly",
                scenario_effect=ScenarioEffect(
                    transaction_value_median_multiplier=2.0,
                    transaction_value_sigma_multiplier=1.0,
                    recent_login_failure_rate_increment=0.0,
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="population"):
        generate_synthetic_dataset_v3(
            seed=42,
            quantidade=20,
            inicio=datetime(2026, 1, 1, 0, 0),
            fim=datetime(2026, 1, 8, 0, 0),
            misturas=[
                ScenarioMix(
                    cenario=obter_cenario("transaction_anomaly"),
                    proporcao=1.0,
                ),
            ],
            label_policy=OperationalLabelPolicy(
                probabilidade_falso_positivo=0.0,
                probabilidade_falso_negativo=0.0,
            ),
            generation_config=generation_config,
        )


def test_generate_synthetic_dataset_v3_rejeita_scenario_config_ausente_das_misturas():
    generation_config = SyntheticGenerationConfig(
        scenario_configs=(
            ScenarioGenerationConfig(
                scenario="credential_attack",
                intensity_policy=EventIntensityPolicy(
                    intensity_min=0.20,
                    intensity_max=0.80,
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="scenario_configs"):
        generate_synthetic_dataset_v3(
            seed=42,
            quantidade=20,
            inicio=datetime(2026, 1, 1, 0, 0),
            fim=datetime(2026, 1, 8, 0, 0),
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
            generation_config=generation_config,
        )


def test_generate_synthetic_dataset_v3_aceita_scenario_config_parcial():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    population_config = PopulationGenerationConfig(
        customer_count=1,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.0,
        transaction_value_sigma=0.10,
        recent_login_failure_rate_mean=0.0,
        recent_login_failure_rate_shape=2.0,
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("credential_attack"),
            proporcao=0.50,
        ),
        ScenarioMix(
            cenario=obter_cenario("transaction_anomaly"),
            proporcao=0.50,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    referencia = generate_synthetic_dataset_v3(
        seed=2026,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
        ),
    )

    modulado = generate_synthetic_dataset_v3(
        seed=2026,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="transaction_anomaly",
                    scenario_effect=ScenarioEffect(
                        transaction_value_median_multiplier=2.0,
                        transaction_value_sigma_multiplier=1.0,
                        recent_login_failure_rate_increment=0.0,
                    ),
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=1.0,
                        intensity_max=1.0,
                    ),
                ),
            ),
        ),
    )

    credential_referencia = [
        registro
        for registro in referencia.records
        if registro.truth.scenario == "credential_attack"
    ]
    credential_modulado = [
        registro
        for registro in modulado.records
        if registro.truth.scenario == "credential_attack"
    ]

    assert credential_modulado == credential_referencia

    transaction_referencia = [
        registro
        for registro in referencia.records
        if registro.truth.scenario == "transaction_anomaly"
    ]
    transaction_modulado = [
        registro
        for registro in modulado.records
        if registro.truth.scenario == "transaction_anomaly"
    ]

    assert all(
        modulado_registro.observables["valor_transacao"]
        > referencia_registro.observables["valor_transacao"]
        for referencia_registro, modulado_registro in zip(
            transaction_referencia,
            transaction_modulado,
            strict=True,
        )
    )

    assert {registro.truth.event_intensity for registro in transaction_modulado} == {
        1.0
    }

    assert tuple(
        scenario.scenario for scenario in modulado.manifest.generation.scenarios
    ) == ("transaction_anomaly",)


def test_generate_synthetic_dataset_v3_aceita_intensity_sem_scenario_effect_e_sem_population():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("credential_attack"),
            proporcao=1.0,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    referencia = generate_synthetic_dataset_v3(
        seed=314,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(),
    )

    com_intensity = generate_synthetic_dataset_v3(
        seed=314,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="credential_attack",
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=0.50,
                        intensity_max=0.50,
                    ),
                ),
            ),
        ),
    )

    assert [registro.observables for registro in com_intensity.records] == [
        registro.observables for registro in referencia.records
    ]

    assert [registro.operational_labels for registro in com_intensity.records] == [
        registro.operational_labels for registro in referencia.records
    ]

    assert all(
        registro.truth.event_intensity is None for registro in referencia.records
    )

    assert {registro.truth.event_intensity for registro in com_intensity.records} == {
        0.5
    }

    assert len(com_intensity.manifest.generation.scenarios) == 1

    scenario_manifest = com_intensity.manifest.generation.scenarios[0]

    assert scenario_manifest.scenario == "credential_attack"
    assert scenario_manifest.scenario_effect is None
    assert scenario_manifest.intensity_policy.intensity_min == 0.5
    assert scenario_manifest.intensity_policy.intensity_max == 0.5


def test_generate_synthetic_dataset_v3_aplica_scenario_effect_completo_sem_intensity():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    population_config = PopulationGenerationConfig(
        customer_count=1,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.0,
        transaction_value_sigma=0.10,
        recent_login_failure_rate_mean=0.0,
        recent_login_failure_rate_shape=2.0,
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("transaction_anomaly"),
            proporcao=1.0,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    referencia = generate_synthetic_dataset_v3(
        seed=2718,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
        ),
    )

    com_efeito = generate_synthetic_dataset_v3(
        seed=2718,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="transaction_anomaly",
                    scenario_effect=ScenarioEffect(
                        transaction_value_median_multiplier=2.0,
                        transaction_value_sigma_multiplier=1.0,
                        recent_login_failure_rate_increment=0.0,
                    ),
                ),
            ),
        ),
    )

    valores_referencia = [
        registro.observables["valor_transacao"] for registro in referencia.records
    ]
    valores_com_efeito = [
        registro.observables["valor_transacao"] for registro in com_efeito.records
    ]

    assert all(
        valor_com_efeito > valor_referencia
        for valor_referencia, valor_com_efeito in zip(
            valores_referencia,
            valores_com_efeito,
            strict=True,
        )
    )

    observables_referencia_sem_valor = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in referencia.records
    ]

    observables_com_efeito_sem_valor = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in com_efeito.records
    ]

    assert observables_com_efeito_sem_valor == observables_referencia_sem_valor

    assert all(
        registro.truth.event_intensity is None for registro in com_efeito.records
    )

    scenario_manifest = com_efeito.manifest.generation.scenarios[0]

    assert scenario_manifest.scenario == "transaction_anomaly"
    assert scenario_manifest.scenario_effect.transaction_value_median_multiplier == 2.0
    assert scenario_manifest.intensity_policy is None


def test_generate_synthetic_dataset_v3_e_reprodutivel_com_scenario_config():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    generation_config = SyntheticGenerationConfig(
        population_config=PopulationGenerationConfig(
            customer_count=5,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        ),
        scenario_configs=(
            ScenarioGenerationConfig(
                scenario="account_takeover",
                scenario_effect=ScenarioEffect(
                    transaction_value_median_multiplier=1.5,
                    transaction_value_sigma_multiplier=1.10,
                    recent_login_failure_rate_increment=0.35,
                ),
                intensity_policy=EventIntensityPolicy(
                    intensity_min=0.20,
                    intensity_max=0.80,
                ),
            ),
        ),
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=0.50,
        ),
        ScenarioMix(
            cenario=obter_cenario("account_takeover"),
            proporcao=0.50,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    primeira = generate_synthetic_dataset_v3(
        seed=9090,
        quantidade=80,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    segunda = generate_synthetic_dataset_v3(
        seed=9090,
        quantidade=80,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    assert primeira.records == segunda.records
    assert primeira.manifest == segunda.manifest

    intensidades = [
        registro.truth.event_intensity
        for registro in primeira.records
        if registro.truth.scenario == "account_takeover"
    ]

    assert intensidades
    assert all(
        intensidade is not None and 0.20 <= intensidade <= 0.80
        for intensidade in intensidades
    )


def test_generate_synthetic_dataset_v3_preserva_cenario_posterior_nao_configurado():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    population_config = PopulationGenerationConfig(
        customer_count=5,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("transaction_anomaly"),
            proporcao=0.50,
        ),
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=0.50,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    referencia = generate_synthetic_dataset_v3(
        seed=1618,
        quantidade=80,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
        ),
    )

    configurado = generate_synthetic_dataset_v3(
        seed=1618,
        quantidade=80,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="transaction_anomaly",
                    scenario_effect=ScenarioEffect(
                        transaction_value_median_multiplier=2.0,
                        transaction_value_sigma_multiplier=1.0,
                        recent_login_failure_rate_increment=0.0,
                    ),
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=0.25,
                        intensity_max=0.75,
                    ),
                ),
            ),
        ),
    )

    baseline_referencia = [
        registro
        for registro in referencia.records
        if registro.truth.scenario == "baseline"
    ]

    baseline_configurado = [
        registro
        for registro in configurado.records
        if registro.truth.scenario == "baseline"
    ]

    assert baseline_configurado == baseline_referencia

    transaction_configurado = [
        registro
        for registro in configurado.records
        if registro.truth.scenario == "transaction_anomaly"
    ]

    assert transaction_configurado
    assert all(
        registro.truth.event_intensity is not None
        for registro in transaction_configurado
    )

    assert all(
        registro.truth.event_intensity is None for registro in baseline_configurado
    )
