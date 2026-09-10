from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.dataset import (
    GeneratedSyntheticDataset,
    generate_synthetic_dataset_v3,
)
from src.synthetic.generation_config import SyntheticGenerationConfig
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.manifest import DatasetManifestV2
from src.synthetic.population_generation import PopulationGenerationConfig
from src.synthetic.scenarios import obter_cenario
from src.synthetic.seed_strategy import build_synthetic_seed_plan


def test_generate_synthetic_dataset_v3_integra_population():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    generation_config = SyntheticGenerationConfig(
        population_config=PopulationGenerationConfig(
            customer_count=1,
            transaction_value_median_base=900.0,
            transaction_value_median_log_sigma=0.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.0,
            recent_login_failure_rate_shape=2.0,
        ),
    )

    resultado = generate_synthetic_dataset_v3(
        seed=42,
        quantidade=20,
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
        generation_config=generation_config,
    )

    assert isinstance(resultado, GeneratedSyntheticDataset)
    assert isinstance(resultado.manifest, DatasetManifestV2)

    seed_plan = build_synthetic_seed_plan(42)

    assert resultado.manifest.schema_version == "2"
    assert resultado.manifest.seed == 42
    assert (
        resultado.manifest.generation.seed_strategy.statistical_seed
        == seed_plan.statistical_seed
    )
    assert (
        resultado.manifest.generation.seed_strategy.population_seed
        == seed_plan.population_seed
    )

    assert resultado.manifest.generation.population is not None
    assert resultado.manifest.generation.population.customer_count == 1

    assert {
        registro.observables["cliente_pseudonimo"] for registro in resultado.records
    } == {"cliente-001"}

    assert all(
        registro.observables["falhas_login_recentes"] == 0
        for registro in resultado.records
    )


def test_generate_synthetic_dataset_v3_rejeita_severity_ainda_nao_integrada():
    from src.synthetic.severity import SeverityPolicy

    generation_config = SyntheticGenerationConfig(
        severity_policy=SeverityPolicy(
            normal_min=0.0,
            normal_max=40.0,
            suspicious_min=20.0,
            suspicious_max=100.0,
        ),
    )

    with pytest.raises(ValueError, match="severity_policy"):
        generate_synthetic_dataset_v3(
            seed=42,
            quantidade=10,
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


def test_generate_synthetic_dataset_v3_rejeita_scenario_configs_ainda_nao_integrados():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.scenario_effects import ScenarioEffect

    generation_config = SyntheticGenerationConfig(
        scenario_configs=(
            ScenarioGenerationConfig(
                scenario="baseline",
                scenario_effect=ScenarioEffect(
                    transaction_value_median_multiplier=1.5,
                    transaction_value_sigma_multiplier=1.2,
                    recent_login_failure_rate_increment=0.25,
                ),
            ),
        ),
    )

    with pytest.raises(ValueError, match="scenario_configs"):
        generate_synthetic_dataset_v3(
            seed=42,
            quantidade=10,
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


def test_generate_synthetic_dataset_v3_aceita_generation_config_vazio():
    resultado = generate_synthetic_dataset_v3(
        seed=42,
        quantidade=10,
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
        generation_config=SyntheticGenerationConfig(),
    )

    seed_plan = build_synthetic_seed_plan(42)

    assert isinstance(resultado.manifest, DatasetManifestV2)
    assert resultado.manifest.generation.population is None
    assert resultado.manifest.generation.severity_policy is None
    assert resultado.manifest.generation.scenarios == ()
    assert (
        resultado.manifest.generation.seed_strategy.statistical_seed
        == seed_plan.statistical_seed
    )


@pytest.mark.parametrize(
    "generation_config",
    (
        None,
        123,
        "generation-config",
        object(),
    ),
)
def test_generate_synthetic_dataset_v3_rejeita_generation_config_invalido(
    generation_config,
):
    with pytest.raises(ValueError, match="generation_config"):
        generate_synthetic_dataset_v3(
            seed=42,
            quantidade=10,
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


def test_generate_synthetic_dataset_v3_e_reprodutivel_com_mesma_configuracao():
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
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=1.0,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    primeira = generate_synthetic_dataset_v3(
        seed=777,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    segunda = generate_synthetic_dataset_v3(
        seed=777,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=generation_config,
    )

    assert primeira.records == segunda.records
    assert primeira.manifest == segunda.manifest


def test_generate_synthetic_dataset_v3_population_controla_baseline_transacional():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    config_baixa = SyntheticGenerationConfig(
        population_config=PopulationGenerationConfig(
            customer_count=1,
            transaction_value_median_base=90.0,
            transaction_value_median_log_sigma=0.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.0,
            recent_login_failure_rate_shape=2.0,
        ),
    )

    config_alta = SyntheticGenerationConfig(
        population_config=PopulationGenerationConfig(
            customer_count=1,
            transaction_value_median_base=900.0,
            transaction_value_median_log_sigma=0.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.0,
            recent_login_failure_rate_shape=2.0,
        ),
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=1.0,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    resultado_baixo = generate_synthetic_dataset_v3(
        seed=777,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=config_baixa,
    )

    resultado_alto = generate_synthetic_dataset_v3(
        seed=777,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=config_alta,
    )

    valores_baixos = [
        registro.observables["valor_transacao"] for registro in resultado_baixo.records
    ]
    valores_altos = [
        registro.observables["valor_transacao"] for registro in resultado_alto.records
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

    assert (
        resultado_baixo.manifest.generation.population.transaction_value_median_base
        == 90.0
    )
    assert (
        resultado_alto.manifest.generation.population.transaction_value_median_base
        == 900.0
    )


def test_generate_synthetic_dataset_v3_population_controla_baseline_de_login():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    config_sem_falhas = SyntheticGenerationConfig(
        population_config=PopulationGenerationConfig(
            customer_count=1,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.0,
            recent_login_failure_rate_shape=2.0,
        ),
    )

    config_com_falhas = SyntheticGenerationConfig(
        population_config=PopulationGenerationConfig(
            customer_count=1,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=5.0,
            recent_login_failure_rate_shape=2.0,
        ),
    )

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=1.0,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    resultado_sem_falhas = generate_synthetic_dataset_v3(
        seed=777,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=config_sem_falhas,
    )

    resultado_com_falhas = generate_synthetic_dataset_v3(
        seed=777,
        quantidade=40,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
        generation_config=config_com_falhas,
    )

    falhas_sem_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in resultado_sem_falhas.records
    ]
    falhas_com_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in resultado_com_falhas.records
    ]

    assert all(falhas == 0 for falhas in falhas_sem_baseline)
    assert sum(falhas_com_baseline) > 0
    assert falhas_sem_baseline != falhas_com_baseline

    assert (
        resultado_sem_falhas.manifest.generation.population.recent_login_failure_rate_mean
        == 0.0
    )
    assert (
        resultado_com_falhas.manifest.generation.population.recent_login_failure_rate_mean
        == 5.0
    )
