from datetime import datetime

import pytest

from src.synthetic.composer import ScenarioMix
from src.synthetic.generation_config import SyntheticGenerationConfig
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.manifest import DatasetManifestV2
from src.synthetic.manifest_builder import build_dataset_manifest_v2
from src.synthetic.scenarios import obter_cenario
from src.synthetic.seed_strategy import SyntheticSeedPlan


def test_build_dataset_manifest_v2_cria_snapshot_basico():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    seed_plan = SyntheticSeedPlan(
        root_seed=42,
        statistical_seed=101,
        population_seed=202,
    )

    manifest = build_dataset_manifest_v2(
        seed_plan=seed_plan,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=1.0,
            ),
        ],
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=0.20,
            probabilidade_falso_negativo=0.30,
        ),
        generation_config=SyntheticGenerationConfig(),
    )

    assert isinstance(manifest, DatasetManifestV2)
    assert manifest.schema_version == "2"
    assert manifest.seed == 42
    assert manifest.quantidade == 10
    assert manifest.inicio == inicio
    assert manifest.fim == fim

    assert len(manifest.scenarios) == 1
    assert manifest.scenarios[0].scenario == "baseline"
    assert manifest.scenarios[0].configured_proportion == 1.0
    assert manifest.scenarios[0].allocated_quantity == 10

    assert manifest.label_policy.false_positive_probability == 0.20
    assert manifest.label_policy.false_negative_probability == 0.30

    assert manifest.generation.seed_strategy.strategy_version == "1"
    assert manifest.generation.seed_strategy.statistical_seed == 101
    assert manifest.generation.seed_strategy.population_seed == 202
    assert manifest.generation.population is None
    assert manifest.generation.severity_policy is None
    assert manifest.generation.scenarios == ()


@pytest.mark.parametrize(
    "seed_plan",
    (
        123,
        "seed-plan",
        object(),
        None,
    ),
)
def test_build_dataset_manifest_v2_rejeita_seed_plan_invalido(
    seed_plan,
):
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    with pytest.raises(ValueError, match="seed_plan"):
        build_dataset_manifest_v2(
            seed_plan=seed_plan,
            quantidade=10,
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
            generation_config=SyntheticGenerationConfig(),
        )


@pytest.mark.parametrize(
    "generation_config",
    (
        123,
        "generation-config",
        object(),
        None,
    ),
)
def test_build_dataset_manifest_v2_rejeita_generation_config_invalida(
    generation_config,
):
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    seed_plan = SyntheticSeedPlan(
        root_seed=42,
        statistical_seed=101,
        population_seed=202,
    )

    with pytest.raises(ValueError, match="config"):
        build_dataset_manifest_v2(
            seed_plan=seed_plan,
            quantidade=10,
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


def test_build_dataset_manifest_v2_preserva_generation_provenance_composta():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.intensity import EventIntensityPolicy
    from src.synthetic.population_generation import PopulationGenerationConfig
    from src.synthetic.scenario_effects import ScenarioEffect
    from src.synthetic.severity import SeverityPolicy

    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    population_config = PopulationGenerationConfig(
        customer_count=100,
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

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.2,
        recent_login_failure_rate_increment=0.25,
    )

    intensity_policy = EventIntensityPolicy(
        intensity_min=0.25,
        intensity_max=0.75,
    )

    scenario_config = ScenarioGenerationConfig(
        scenario="credential_attack",
        scenario_effect=scenario_effect,
        intensity_policy=intensity_policy,
    )

    generation_config = SyntheticGenerationConfig(
        population_config=population_config,
        severity_policy=severity_policy,
        scenario_configs=(scenario_config,),
    )

    seed_plan = SyntheticSeedPlan(
        root_seed=42,
        statistical_seed=101,
        population_seed=202,
    )

    manifest = build_dataset_manifest_v2(
        seed_plan=seed_plan,
        quantidade=10,
        inicio=inicio,
        fim=fim,
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
        generation_config=generation_config,
    )

    assert manifest.seed == seed_plan.root_seed

    assert manifest.generation.population is not population_config
    assert manifest.generation.population.customer_count == 100

    assert manifest.generation.severity_policy is not severity_policy
    assert manifest.generation.severity_policy.normal_min == 0.0
    assert manifest.generation.severity_policy.suspicious_max == 100.0

    assert len(manifest.generation.scenarios) == 1

    scenario_manifest = manifest.generation.scenarios[0]

    assert scenario_manifest.scenario == "credential_attack"

    assert scenario_manifest.scenario_effect is not scenario_effect
    assert scenario_manifest.scenario_effect.transaction_value_median_multiplier == 1.5
    assert scenario_manifest.scenario_effect.transaction_value_sigma_multiplier == 1.2
    assert scenario_manifest.scenario_effect.recent_login_failure_rate_increment == 0.25

    assert scenario_manifest.intensity_policy is not intensity_policy
    assert scenario_manifest.intensity_policy.intensity_min == 0.25
    assert scenario_manifest.intensity_policy.intensity_max == 0.75
