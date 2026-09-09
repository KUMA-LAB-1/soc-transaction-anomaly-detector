from .generation_manifest import SeedStrategyManifest
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
