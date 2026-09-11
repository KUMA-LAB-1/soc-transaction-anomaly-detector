from .behavior_flags import BehaviorFlagBaseline
from .generation_config import ScenarioGenerationConfig, SyntheticGenerationConfig
from .generation_manifest import (
    BehaviorFlagBaselineManifest,
    EventIntensityPolicyManifest,
    PopulationGenerationManifest,
    ScenarioEffectManifest,
    ScenarioGenerationManifest,
    SeedStrategyManifest,
    SeverityPolicyManifest,
    SyntheticGenerationManifest,
)
from .intensity import EventIntensityPolicy
from .population_generation import PopulationGenerationConfig
from .scenario_effects import ScenarioEffect
from .seed_strategy import SyntheticSeedPlan
from .severity import SeverityPolicy


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


def build_behavior_flag_baseline_manifest(
    baseline: BehaviorFlagBaseline,
) -> BehaviorFlagBaselineManifest:
    if not isinstance(baseline, BehaviorFlagBaseline):
        raise ValueError("baseline deve ser BehaviorFlagBaseline.")

    return BehaviorFlagBaselineManifest(
        new_device_probability=baseline.new_device_probability,
        limit_change_probability=baseline.limit_change_probability,
        location_change_probability=baseline.location_change_probability,
    )


def build_population_generation_manifest(
    config: PopulationGenerationConfig,
) -> PopulationGenerationManifest:
    if not isinstance(config, PopulationGenerationConfig):
        raise ValueError("config deve ser PopulationGenerationConfig.")

    behavior_flag_baseline = (
        build_behavior_flag_baseline_manifest(config.behavior_flag_baseline)
        if config.behavior_flag_baseline is not None
        else None
    )

    return PopulationGenerationManifest(
        customer_count=config.customer_count,
        transaction_value_median_base=config.transaction_value_median_base,
        transaction_value_median_log_sigma=config.transaction_value_median_log_sigma,
        transaction_value_sigma=config.transaction_value_sigma,
        recent_login_failure_rate_mean=config.recent_login_failure_rate_mean,
        recent_login_failure_rate_shape=config.recent_login_failure_rate_shape,
        behavior_flag_baseline=behavior_flag_baseline,
    )


def build_severity_policy_manifest(
    policy: SeverityPolicy,
) -> SeverityPolicyManifest:
    if not isinstance(policy, SeverityPolicy):
        raise ValueError("policy deve ser SeverityPolicy.")

    return SeverityPolicyManifest(
        normal_min=policy.normal_min,
        normal_max=policy.normal_max,
        suspicious_min=policy.suspicious_min,
        suspicious_max=policy.suspicious_max,
    )


def build_event_intensity_policy_manifest(
    policy: EventIntensityPolicy,
) -> EventIntensityPolicyManifest:
    if not isinstance(policy, EventIntensityPolicy):
        raise ValueError("policy deve ser EventIntensityPolicy.")

    return EventIntensityPolicyManifest(
        intensity_min=policy.intensity_min,
        intensity_max=policy.intensity_max,
    )


def build_scenario_effect_manifest(
    effect: ScenarioEffect,
) -> ScenarioEffectManifest:
    if not isinstance(effect, ScenarioEffect):
        raise ValueError("effect deve ser ScenarioEffect.")

    return ScenarioEffectManifest(
        transaction_value_median_multiplier=(
            effect.transaction_value_median_multiplier
        ),
        transaction_value_sigma_multiplier=(effect.transaction_value_sigma_multiplier),
        recent_login_failure_rate_increment=(
            effect.recent_login_failure_rate_increment
        ),
        new_device_probability_delta=effect.new_device_probability_delta,
        limit_change_probability_delta=effect.limit_change_probability_delta,
        location_change_probability_delta=effect.location_change_probability_delta,
    )


def build_scenario_generation_manifest(
    config: ScenarioGenerationConfig,
) -> ScenarioGenerationManifest:
    if not isinstance(config, ScenarioGenerationConfig):
        raise ValueError("config deve ser ScenarioGenerationConfig.")

    scenario_effect = (
        build_scenario_effect_manifest(config.scenario_effect)
        if config.scenario_effect is not None
        else None
    )

    intensity_policy = (
        build_event_intensity_policy_manifest(config.intensity_policy)
        if config.intensity_policy is not None
        else None
    )

    return ScenarioGenerationManifest(
        scenario=config.scenario,
        scenario_effect=scenario_effect,
        intensity_policy=intensity_policy,
    )


def build_synthetic_generation_manifest(
    *,
    config: SyntheticGenerationConfig,
    seed_plan: SyntheticSeedPlan,
) -> SyntheticGenerationManifest:
    if not isinstance(config, SyntheticGenerationConfig):
        raise ValueError("config deve ser SyntheticGenerationConfig.")

    population = (
        build_population_generation_manifest(config.population_config)
        if config.population_config is not None
        else None
    )

    severity_policy = (
        build_severity_policy_manifest(config.severity_policy)
        if config.severity_policy is not None
        else None
    )

    scenarios = tuple(
        build_scenario_generation_manifest(scenario_config)
        for scenario_config in config.scenario_configs
    )

    return SyntheticGenerationManifest(
        seed_strategy=build_seed_strategy_manifest(seed_plan),
        population=population,
        severity_policy=severity_policy,
        scenarios=scenarios,
    )
