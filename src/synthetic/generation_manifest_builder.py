from .generation_manifest import (
    PopulationGenerationManifest,
    SeedStrategyManifest,
)
from .population_generation import PopulationGenerationConfig
from .seed_strategy import SyntheticSeedPlan


def build_seed_strategy_manifest(
    seed_plan: SyntheticSeedPlan,
) -> SeedStrategyManifest:
    if not isinstance(seed_plan, SyntheticSeedPlan):
        raise ValueError("seed_plan deve ser SyntheticSeedPlan.")

    return SeedStrategyManifest(
        strategy_version="1",
        statistical_seed=seed_plan.statistical_seed,
        population_seed=seed_plan.population_seed,
    )


def build_population_generation_manifest(
    config: PopulationGenerationConfig,
) -> PopulationGenerationManifest:
    if not isinstance(config, PopulationGenerationConfig):
        raise ValueError("config deve ser PopulationGenerationConfig.")

    return PopulationGenerationManifest(
        customer_count=config.customer_count,
        transaction_value_median_base=config.transaction_value_median_base,
        transaction_value_median_log_sigma=config.transaction_value_median_log_sigma,
        transaction_value_sigma=config.transaction_value_sigma,
        recent_login_failure_rate_mean=config.recent_login_failure_rate_mean,
        recent_login_failure_rate_shape=config.recent_login_failure_rate_shape,
    )
