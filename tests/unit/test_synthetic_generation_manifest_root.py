import pytest


def test_synthetic_generation_manifest_preserva_snapshot_basico():
    from src.synthetic.generation_manifest import (
        SeedStrategyManifest,
        SyntheticGenerationManifest,
    )

    seed_strategy = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=101,
        population_seed=202,
    )

    manifest = SyntheticGenerationManifest(
        seed_strategy=seed_strategy,
    )

    assert manifest.seed_strategy is seed_strategy
    assert manifest.population is None
    assert manifest.severity_policy is None
    assert manifest.scenarios == ()


@pytest.mark.parametrize(
    "seed_strategy",
    (
        123,
        "seed-strategy",
        object(),
        None,
    ),
)
def test_synthetic_generation_manifest_rejeita_seed_strategy_invalida(
    seed_strategy,
):
    from src.synthetic.generation_manifest import SyntheticGenerationManifest

    with pytest.raises(ValueError, match="seed_strategy"):
        SyntheticGenerationManifest(
            seed_strategy=seed_strategy,
        )


@pytest.mark.parametrize(
    "population",
    (
        123,
        "population",
        object(),
    ),
)
def test_synthetic_generation_manifest_rejeita_population_invalida(
    population,
):
    from src.synthetic.generation_manifest import (
        SeedStrategyManifest,
        SyntheticGenerationManifest,
    )

    seed_strategy = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=101,
        population_seed=202,
    )

    with pytest.raises(ValueError, match="population"):
        SyntheticGenerationManifest(
            seed_strategy=seed_strategy,
            population=population,
        )


@pytest.mark.parametrize(
    "severity_policy",
    (
        123,
        "severity",
        object(),
    ),
)
def test_synthetic_generation_manifest_rejeita_severity_policy_invalida(
    severity_policy,
):
    from src.synthetic.generation_manifest import (
        SeedStrategyManifest,
        SyntheticGenerationManifest,
    )

    seed_strategy = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=101,
        population_seed=202,
    )

    with pytest.raises(ValueError, match="severity_policy"):
        SyntheticGenerationManifest(
            seed_strategy=seed_strategy,
            severity_policy=severity_policy,
        )


@pytest.mark.parametrize(
    "scenarios",
    (
        [],
        ["account_takeover"],
        "account_takeover",
        None,
    ),
)
def test_synthetic_generation_manifest_rejeita_scenarios_que_nao_sao_tuple(
    scenarios,
):
    from src.synthetic.generation_manifest import (
        SeedStrategyManifest,
        SyntheticGenerationManifest,
    )

    seed_strategy = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=101,
        population_seed=202,
    )

    with pytest.raises(ValueError, match="scenarios"):
        SyntheticGenerationManifest(
            seed_strategy=seed_strategy,
            scenarios=scenarios,
        )


@pytest.mark.parametrize(
    "scenario",
    (
        123,
        "account_takeover",
        object(),
        None,
    ),
)
def test_synthetic_generation_manifest_rejeita_item_invalido_em_scenarios(
    scenario,
):
    from src.synthetic.generation_manifest import (
        SeedStrategyManifest,
        SyntheticGenerationManifest,
    )

    seed_strategy = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=101,
        population_seed=202,
    )

    with pytest.raises(ValueError, match="scenarios"):
        SyntheticGenerationManifest(
            seed_strategy=seed_strategy,
            scenarios=(scenario,),
        )


def test_synthetic_generation_manifest_rejeita_scenarios_duplicados():
    from src.synthetic.generation_manifest import (
        ScenarioGenerationManifest,
        SeedStrategyManifest,
        SyntheticGenerationManifest,
    )

    seed_strategy = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=101,
        population_seed=202,
    )

    primeiro = ScenarioGenerationManifest(
        scenario="account_takeover",
    )

    segundo = ScenarioGenerationManifest(
        scenario="account_takeover",
    )

    with pytest.raises(ValueError, match="scenarios"):
        SyntheticGenerationManifest(
            seed_strategy=seed_strategy,
            scenarios=(
                primeiro,
                segundo,
            ),
        )


def test_synthetic_generation_manifest_preserva_ordem_dos_scenarios():
    from src.synthetic.generation_manifest import (
        ScenarioGenerationManifest,
        SeedStrategyManifest,
        SyntheticGenerationManifest,
    )

    seed_strategy = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=101,
        population_seed=202,
    )

    primeiro = ScenarioGenerationManifest(
        scenario="credential_attack",
    )

    segundo = ScenarioGenerationManifest(
        scenario="account_takeover",
    )

    manifest = SyntheticGenerationManifest(
        seed_strategy=seed_strategy,
        scenarios=(
            primeiro,
            segundo,
        ),
    )

    assert manifest.scenarios == (
        primeiro,
        segundo,
    )


def test_synthetic_generation_manifest_e_imutavel():
    from dataclasses import FrozenInstanceError

    from src.synthetic.generation_manifest import (
        SeedStrategyManifest,
        SyntheticGenerationManifest,
    )

    seed_strategy = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=101,
        population_seed=202,
    )

    manifest = SyntheticGenerationManifest(
        seed_strategy=seed_strategy,
    )

    with pytest.raises(FrozenInstanceError):
        manifest.scenarios = ()


def test_build_synthetic_generation_manifest_cria_snapshot_basico():
    from src.synthetic.generation_config import SyntheticGenerationConfig
    from src.synthetic.generation_manifest_builder import (
        build_synthetic_generation_manifest,
    )
    from src.synthetic.seed_strategy import SyntheticSeedPlan

    config = SyntheticGenerationConfig()

    seed_plan = SyntheticSeedPlan(
        root_seed=42,
        statistical_seed=101,
        population_seed=202,
    )

    manifest = build_synthetic_generation_manifest(
        config=config,
        seed_plan=seed_plan,
    )

    assert manifest.seed_strategy.strategy_version == "1"
    assert manifest.seed_strategy.statistical_seed == 101
    assert manifest.seed_strategy.population_seed == 202

    assert manifest.population is None
    assert manifest.severity_policy is None
    assert manifest.scenarios == ()


def test_build_synthetic_generation_manifest_materializa_population():
    from src.synthetic.generation_config import SyntheticGenerationConfig
    from src.synthetic.generation_manifest import PopulationGenerationManifest
    from src.synthetic.generation_manifest_builder import (
        build_synthetic_generation_manifest,
    )
    from src.synthetic.population_generation import PopulationGenerationConfig
    from src.synthetic.seed_strategy import SyntheticSeedPlan

    population_config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    config = SyntheticGenerationConfig(
        population_config=population_config,
    )

    seed_plan = SyntheticSeedPlan(
        root_seed=42,
        statistical_seed=101,
        population_seed=202,
    )

    manifest = build_synthetic_generation_manifest(
        config=config,
        seed_plan=seed_plan,
    )

    assert isinstance(
        manifest.population,
        PopulationGenerationManifest,
    )
    assert manifest.population is not population_config
    assert manifest.population.customer_count == population_config.customer_count
    assert (
        manifest.population.transaction_value_median_base
        == population_config.transaction_value_median_base
    )
    assert (
        manifest.population.transaction_value_median_log_sigma
        == population_config.transaction_value_median_log_sigma
    )
    assert (
        manifest.population.transaction_value_sigma
        == population_config.transaction_value_sigma
    )
    assert (
        manifest.population.recent_login_failure_rate_mean
        == population_config.recent_login_failure_rate_mean
    )
    assert (
        manifest.population.recent_login_failure_rate_shape
        == population_config.recent_login_failure_rate_shape
    )


def test_build_synthetic_generation_manifest_materializa_severity_policy():
    from src.synthetic.generation_config import SyntheticGenerationConfig
    from src.synthetic.generation_manifest import SeverityPolicyManifest
    from src.synthetic.generation_manifest_builder import (
        build_synthetic_generation_manifest,
    )
    from src.synthetic.seed_strategy import SyntheticSeedPlan
    from src.synthetic.severity import SeverityPolicy

    severity_policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    config = SyntheticGenerationConfig(
        severity_policy=severity_policy,
    )

    seed_plan = SyntheticSeedPlan(
        root_seed=42,
        statistical_seed=101,
        population_seed=202,
    )

    manifest = build_synthetic_generation_manifest(
        config=config,
        seed_plan=seed_plan,
    )

    assert isinstance(
        manifest.severity_policy,
        SeverityPolicyManifest,
    )
    assert manifest.severity_policy is not severity_policy
    assert manifest.severity_policy.normal_min == severity_policy.normal_min
    assert manifest.severity_policy.normal_max == severity_policy.normal_max
    assert manifest.severity_policy.suspicious_min == severity_policy.suspicious_min
    assert manifest.severity_policy.suspicious_max == severity_policy.suspicious_max


def test_build_synthetic_generation_manifest_materializa_scenarios_preservando_ordem():
    from src.synthetic.generation_config import (
        ScenarioGenerationConfig,
        SyntheticGenerationConfig,
    )
    from src.synthetic.generation_manifest import ScenarioGenerationManifest
    from src.synthetic.generation_manifest_builder import (
        build_synthetic_generation_manifest,
    )
    from src.synthetic.seed_strategy import SyntheticSeedPlan

    primeiro = ScenarioGenerationConfig(
        scenario="credential_attack",
    )

    segundo = ScenarioGenerationConfig(
        scenario="account_takeover",
    )

    config = SyntheticGenerationConfig(
        scenario_configs=(
            primeiro,
            segundo,
        ),
    )

    seed_plan = SyntheticSeedPlan(
        root_seed=42,
        statistical_seed=101,
        population_seed=202,
    )

    manifest = build_synthetic_generation_manifest(
        config=config,
        seed_plan=seed_plan,
    )

    assert len(manifest.scenarios) == 2
    assert all(
        isinstance(scenario, ScenarioGenerationManifest)
        for scenario in manifest.scenarios
    )
    assert tuple(scenario.scenario for scenario in manifest.scenarios) == (
        "credential_attack",
        "account_takeover",
    )

    assert manifest.scenarios[0] is not primeiro
    assert manifest.scenarios[1] is not segundo


@pytest.mark.parametrize(
    "config",
    (
        123,
        "synthetic-config",
        object(),
        None,
    ),
)
def test_build_synthetic_generation_manifest_rejeita_config_invalida(
    config,
):
    from src.synthetic.generation_manifest_builder import (
        build_synthetic_generation_manifest,
    )
    from src.synthetic.seed_strategy import SyntheticSeedPlan

    seed_plan = SyntheticSeedPlan(
        root_seed=42,
        statistical_seed=101,
        population_seed=202,
    )

    with pytest.raises(ValueError, match="config"):
        build_synthetic_generation_manifest(
            config=config,
            seed_plan=seed_plan,
        )


@pytest.mark.parametrize(
    "seed_plan",
    (
        123,
        "seed-plan",
        object(),
        None,
    ),
)
def test_build_synthetic_generation_manifest_rejeita_seed_plan_invalido(
    seed_plan,
):
    from src.synthetic.generation_config import SyntheticGenerationConfig
    from src.synthetic.generation_manifest_builder import (
        build_synthetic_generation_manifest,
    )

    config = SyntheticGenerationConfig()

    with pytest.raises(ValueError, match="seed_plan"):
        build_synthetic_generation_manifest(
            config=config,
            seed_plan=seed_plan,
        )
