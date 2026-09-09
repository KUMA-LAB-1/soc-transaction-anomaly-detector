import math
from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.generation_manifest import SeedStrategyManifest


def test_seed_strategy_manifest_preserva_snapshot_da_estrategia():
    manifest = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=123,
        population_seed=456,
    )

    assert manifest.strategy_version == "1"
    assert manifest.statistical_seed == 123
    assert manifest.population_seed == 456


@pytest.mark.parametrize(
    "strategy_version",
    (
        "",
        "   ",
        None,
        1,
    ),
)
def test_seed_strategy_manifest_rejeita_strategy_version_invalida(
    strategy_version,
):
    with pytest.raises(ValueError, match="strategy_version"):
        SeedStrategyManifest(
            strategy_version=strategy_version,
            statistical_seed=123,
            population_seed=456,
        )


@pytest.mark.parametrize(
    "statistical_seed",
    (
        -1,
        True,
        1.5,
        "123",
        None,
    ),
)
def test_seed_strategy_manifest_rejeita_statistical_seed_invalido(
    statistical_seed,
):
    with pytest.raises(ValueError, match="statistical_seed"):
        SeedStrategyManifest(
            strategy_version="1",
            statistical_seed=statistical_seed,
            population_seed=456,
        )


@pytest.mark.parametrize(
    "population_seed",
    (
        -1,
        True,
        1.5,
        "456",
        None,
    ),
)
def test_seed_strategy_manifest_rejeita_population_seed_invalido(
    population_seed,
):
    with pytest.raises(ValueError, match="population_seed"):
        SeedStrategyManifest(
            strategy_version="1",
            statistical_seed=123,
            population_seed=population_seed,
        )


def test_seed_strategy_manifest_e_imutavel():
    manifest = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=123,
        population_seed=456,
    )

    with pytest.raises(FrozenInstanceError):
        manifest.statistical_seed = 789


def test_seed_strategy_manifest_aceita_seeds_zero():
    manifest = SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=0,
        population_seed=0,
    )

    assert manifest.statistical_seed == 0
    assert manifest.population_seed == 0


def test_build_seed_strategy_manifest_cria_snapshot_do_seed_plan():
    from src.synthetic.generation_manifest_builder import (
        build_seed_strategy_manifest,
    )
    from src.synthetic.seed_strategy import build_synthetic_seed_plan

    seed_plan = build_synthetic_seed_plan(42)

    manifest = build_seed_strategy_manifest(seed_plan)

    assert manifest.strategy_version == "1"
    assert manifest.statistical_seed == seed_plan.statistical_seed
    assert manifest.population_seed == seed_plan.population_seed
    assert manifest is not seed_plan


@pytest.mark.parametrize(
    "seed_plan",
    (
        123,
        "seed-plan",
        object(),
        None,
    ),
)
def test_build_seed_strategy_manifest_rejeita_seed_plan_invalido(
    seed_plan,
):
    from src.synthetic.generation_manifest_builder import (
        build_seed_strategy_manifest,
    )

    with pytest.raises(ValueError, match="seed_plan"):
        build_seed_strategy_manifest(seed_plan)


def test_population_generation_manifest_preserva_snapshot_da_configuracao():
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    manifest = PopulationGenerationManifest(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    assert manifest.customer_count == 100
    assert manifest.transaction_value_median_base == 180.0
    assert manifest.transaction_value_median_log_sigma == 0.75
    assert manifest.transaction_value_sigma == 0.65
    assert manifest.recent_login_failure_rate_mean == 0.15
    assert manifest.recent_login_failure_rate_shape == 2.0


@pytest.mark.parametrize(
    "customer_count",
    (
        0,
        -1,
        True,
        1.5,
        "100",
        None,
    ),
)
def test_population_generation_manifest_rejeita_customer_count_invalido(
    customer_count,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="customer_count"):
        PopulationGenerationManifest(
            customer_count=customer_count,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "transaction_value_median_base",
    (
        0.0,
        -1.0,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "180.0",
        None,
    ),
)
def test_population_generation_manifest_rejeita_transaction_value_median_base_invalida(
    transaction_value_median_base,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="transaction_value_median_base"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=transaction_value_median_base,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "transaction_value_median_log_sigma",
    (
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "0.75",
        None,
    ),
)
def test_population_generation_manifest_rejeita_transaction_value_median_log_sigma_invalido(
    transaction_value_median_log_sigma,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="transaction_value_median_log_sigma"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=transaction_value_median_log_sigma,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "transaction_value_sigma",
    (
        0.0,
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "0.65",
        None,
    ),
)
def test_population_generation_manifest_rejeita_transaction_value_sigma_invalido(
    transaction_value_sigma,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="transaction_value_sigma"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=transaction_value_sigma,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "recent_login_failure_rate_mean",
    (
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "0.15",
        None,
    ),
)
def test_population_generation_manifest_rejeita_recent_login_failure_rate_mean_invalida(
    recent_login_failure_rate_mean,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="recent_login_failure_rate_mean"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=recent_login_failure_rate_mean,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "recent_login_failure_rate_shape",
    (
        0.0,
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "2.0",
        None,
    ),
)
def test_population_generation_manifest_rejeita_recent_login_failure_rate_shape_invalido(
    recent_login_failure_rate_shape,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="recent_login_failure_rate_shape"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=recent_login_failure_rate_shape,
        )


def test_population_generation_manifest_aceita_limites_zero_permitidos():
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    manifest = PopulationGenerationManifest(
        customer_count=1,
        transaction_value_median_base=1.0,
        transaction_value_median_log_sigma=0.0,
        transaction_value_sigma=0.1,
        recent_login_failure_rate_mean=0.0,
        recent_login_failure_rate_shape=1.0,
    )

    assert manifest.transaction_value_median_log_sigma == 0.0
    assert manifest.recent_login_failure_rate_mean == 0.0


def test_population_generation_manifest_e_imutavel():
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    manifest = PopulationGenerationManifest(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    with pytest.raises(FrozenInstanceError):
        manifest.customer_count = 200


def test_build_population_generation_manifest_cria_snapshot_da_configuracao():
    from src.synthetic.generation_manifest_builder import (
        build_population_generation_manifest,
    )
    from src.synthetic.population_generation import PopulationGenerationConfig

    config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    manifest = build_population_generation_manifest(config)

    assert manifest.customer_count == config.customer_count
    assert (
        manifest.transaction_value_median_base == config.transaction_value_median_base
    )
    assert (
        manifest.transaction_value_median_log_sigma
        == config.transaction_value_median_log_sigma
    )
    assert manifest.transaction_value_sigma == config.transaction_value_sigma
    assert (
        manifest.recent_login_failure_rate_mean == config.recent_login_failure_rate_mean
    )
    assert (
        manifest.recent_login_failure_rate_shape
        == config.recent_login_failure_rate_shape
    )
    assert manifest is not config


@pytest.mark.parametrize(
    "config",
    (
        123,
        "population-config",
        object(),
        None,
    ),
)
def test_build_population_generation_manifest_rejeita_config_invalida(
    config,
):
    from src.synthetic.generation_manifest_builder import (
        build_population_generation_manifest,
    )

    with pytest.raises(ValueError, match="config"):
        build_population_generation_manifest(config)
