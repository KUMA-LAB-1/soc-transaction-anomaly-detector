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
