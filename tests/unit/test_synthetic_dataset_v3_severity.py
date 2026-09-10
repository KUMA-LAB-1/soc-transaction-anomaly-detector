from datetime import datetime

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import generate_synthetic_dataset_v3
from src.synthetic.generation_config import SyntheticGenerationConfig
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario
from src.synthetic.severity import SeverityPolicy


def test_generate_synthetic_dataset_v3_integra_severity_policy():
    severity_policy = SeverityPolicy(
        normal_min=12.0,
        normal_max=12.0,
        suspicious_min=88.0,
        suspicious_max=88.0,
    )

    resultado = generate_synthetic_dataset_v3(
        seed=42,
        quantidade=20,
        inicio=datetime(2026, 1, 1, 0, 0),
        fim=datetime(2026, 1, 8, 0, 0),
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
        generation_config=SyntheticGenerationConfig(
            severity_policy=severity_policy,
        ),
    )

    baseline_scores = {
        registro.truth.severity_score
        for registro in resultado.records
        if registro.truth.scenario == "baseline"
    }

    suspicious_scores = {
        registro.truth.severity_score
        for registro in resultado.records
        if registro.truth.scenario == "credential_attack"
    }

    assert baseline_scores == {12.0}
    assert suspicious_scores == {88.0}

    severity_manifest = resultado.manifest.generation.severity_policy

    assert severity_manifest is not None
    assert severity_manifest.normal_min == 12.0
    assert severity_manifest.normal_max == 12.0
    assert severity_manifest.suspicious_min == 88.0
    assert severity_manifest.suspicious_max == 88.0


def test_generate_synthetic_dataset_v3_intensity_determina_severity_com_scenario_effect():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.intensity import EventIntensityPolicy
    from src.synthetic.population_generation import PopulationGenerationConfig
    from src.synthetic.scenario_effects import ScenarioEffect

    resultado = generate_synthetic_dataset_v3(
        seed=9090,
        quantidade=40,
        inicio=datetime(2026, 1, 1, 0, 0),
        fim=datetime(2026, 1, 8, 0, 0),
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=1.0,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.0,
            probabilidade_falso_negativo=0.0,
        ),
        generation_config=SyntheticGenerationConfig(
            population_config=PopulationGenerationConfig(
                customer_count=1,
                transaction_value_median_base=180.0,
                transaction_value_median_log_sigma=0.0,
                transaction_value_sigma=0.65,
                recent_login_failure_rate_mean=0.0,
                recent_login_failure_rate_shape=2.0,
            ),
            severity_policy=SeverityPolicy(
                normal_min=0.0,
                normal_max=40.0,
                suspicious_min=20.0,
                suspicious_max=100.0,
            ),
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="credential_attack",
                    scenario_effect=ScenarioEffect(
                        transaction_value_median_multiplier=2.0,
                        transaction_value_sigma_multiplier=1.0,
                        recent_login_failure_rate_increment=1.0,
                    ),
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=0.5,
                        intensity_max=0.5,
                    ),
                ),
            ),
        ),
    )

    assert {registro.truth.event_intensity for registro in resultado.records} == {0.5}

    assert {registro.truth.severity_score for registro in resultado.records} == {60.0}

    scenario_manifest = resultado.manifest.generation.scenarios[0]

    assert scenario_manifest.scenario == "credential_attack"
    assert scenario_manifest.intensity_policy.intensity_min == 0.5
    assert scenario_manifest.intensity_policy.intensity_max == 0.5
    assert resultado.manifest.generation.severity_policy.suspicious_min == 20.0
    assert resultado.manifest.generation.severity_policy.suspicious_max == 100.0


def test_generate_synthetic_dataset_v3_intensity_sem_effect_preserva_sequencia_de_severity():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.intensity import EventIntensityPolicy

    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("account_takeover"),
            proporcao=1.0,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    referencia = generate_synthetic_dataset_v3(
        seed=2718,
        quantidade=60,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            severity_policy=severity_policy,
        ),
    )

    com_intensity = generate_synthetic_dataset_v3(
        seed=2718,
        quantidade=60,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            severity_policy=severity_policy,
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="account_takeover",
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=0.5,
                        intensity_max=0.5,
                    ),
                ),
            ),
        ),
    )

    scores_referencia = [
        registro.truth.severity_score for registro in referencia.records
    ]

    scores_com_intensity = [
        registro.truth.severity_score for registro in com_intensity.records
    ]

    assert scores_com_intensity == scores_referencia

    assert all(
        registro.truth.event_intensity is None for registro in referencia.records
    )

    assert {registro.truth.event_intensity for registro in com_intensity.records} == {
        0.5
    }

    assert [registro.observables for registro in com_intensity.records] == [
        registro.observables for registro in referencia.records
    ]


def test_generate_synthetic_dataset_v3_scenario_effect_sem_intensity_preserva_sequencia_de_severity():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.population_generation import PopulationGenerationConfig
    from src.synthetic.scenario_effects import ScenarioEffect

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

    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
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
        seed=2468,
        quantidade=50,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            severity_policy=severity_policy,
        ),
    )

    com_efeito = generate_synthetic_dataset_v3(
        seed=2468,
        quantidade=50,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            severity_policy=severity_policy,
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

    scores_referencia = [
        registro.truth.severity_score for registro in referencia.records
    ]

    scores_com_efeito = [
        registro.truth.severity_score for registro in com_efeito.records
    ]

    assert scores_com_efeito == scores_referencia

    assert all(
        registro.truth.event_intensity is None for registro in com_efeito.records
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


def test_generate_synthetic_dataset_v3_intensity_zero_neutraliza_effect_sem_acoplar_severity():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.intensity import EventIntensityPolicy
    from src.synthetic.population_generation import PopulationGenerationConfig
    from src.synthetic.scenario_effects import ScenarioEffect

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

    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
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
        seed=97531,
        quantidade=50,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            severity_policy=severity_policy,
        ),
    )

    neutralizado = generate_synthetic_dataset_v3(
        seed=97531,
        quantidade=50,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            severity_policy=severity_policy,
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="transaction_anomaly",
                    scenario_effect=ScenarioEffect(
                        transaction_value_median_multiplier=2.0,
                        transaction_value_sigma_multiplier=1.0,
                        recent_login_failure_rate_increment=0.0,
                    ),
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=0.0,
                        intensity_max=0.0,
                    ),
                ),
            ),
        ),
    )

    assert [registro.observables for registro in neutralizado.records] == [
        registro.observables for registro in referencia.records
    ]

    assert [registro.truth.severity_score for registro in neutralizado.records] == [
        registro.truth.severity_score for registro in referencia.records
    ]

    assert {registro.truth.event_intensity for registro in neutralizado.records} == {
        0.0
    }

    assert all(
        registro.truth.event_intensity is None for registro in referencia.records
    )


def test_generate_synthetic_dataset_v3_modo_causal_preserva_severity_de_cenario_posterior():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.intensity import EventIntensityPolicy
    from src.synthetic.population_generation import PopulationGenerationConfig
    from src.synthetic.scenario_effects import ScenarioEffect

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

    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
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
        seed=12345,
        quantidade=80,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            severity_policy=severity_policy,
        ),
    )

    causal = generate_synthetic_dataset_v3(
        seed=12345,
        quantidade=80,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=SyntheticGenerationConfig(
            population_config=population_config,
            severity_policy=severity_policy,
            scenario_configs=(
                ScenarioGenerationConfig(
                    scenario="transaction_anomaly",
                    scenario_effect=ScenarioEffect(
                        transaction_value_median_multiplier=2.0,
                        transaction_value_sigma_multiplier=1.0,
                        recent_login_failure_rate_increment=0.0,
                    ),
                    intensity_policy=EventIntensityPolicy(
                        intensity_min=0.5,
                        intensity_max=0.5,
                    ),
                ),
            ),
        ),
    )

    baseline_scores_referencia = [
        registro.truth.severity_score
        for registro in referencia.records
        if registro.truth.scenario == "baseline"
    ]

    baseline_scores_causal = [
        registro.truth.severity_score
        for registro in causal.records
        if registro.truth.scenario == "baseline"
    ]

    assert baseline_scores_causal == baseline_scores_referencia

    transaction_scores_causal = {
        registro.truth.severity_score
        for registro in causal.records
        if registro.truth.scenario == "transaction_anomaly"
    }

    assert transaction_scores_causal == {60.0}


def test_generate_synthetic_dataset_v3_severity_causal_e_reprodutivel():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.intensity import EventIntensityPolicy
    from src.synthetic.population_generation import PopulationGenerationConfig
    from src.synthetic.scenario_effects import ScenarioEffect

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
        severity_policy=SeverityPolicy(
            normal_min=0.0,
            normal_max=40.0,
            suspicious_min=20.0,
            suspicious_max=100.0,
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
        seed=6060,
        quantidade=80,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    segunda = generate_synthetic_dataset_v3(
        seed=6060,
        quantidade=80,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    assert primeira.records == segunda.records
    assert primeira.manifest == segunda.manifest

    assert all(
        registro.truth.severity_score is not None for registro in primeira.records
    )

    assert all(
        registro.truth.event_intensity is not None
        for registro in primeira.records
        if registro.truth.scenario == "account_takeover"
    )
