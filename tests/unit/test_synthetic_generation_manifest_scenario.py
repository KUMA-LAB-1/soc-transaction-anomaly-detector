import pytest


def test_scenario_generation_manifest_preserva_snapshot_basico():
    from src.synthetic.generation_manifest import ScenarioGenerationManifest

    manifest = ScenarioGenerationManifest(
        scenario="account_takeover",
    )

    assert manifest.scenario == "account_takeover"
    assert manifest.scenario_effect is None
    assert manifest.intensity_policy is None


@pytest.mark.parametrize(
    "scenario",
    (
        "",
        "   ",
        None,
        123,
        " account_takeover",
        "account_takeover ",
        "\taccount_takeover",
        "account_takeover\n",
    ),
)
def test_scenario_generation_manifest_rejeita_scenario_invalido(
    scenario,
):
    from src.synthetic.generation_manifest import ScenarioGenerationManifest

    with pytest.raises(ValueError, match="scenario"):
        ScenarioGenerationManifest(
            scenario=scenario,
        )


@pytest.mark.parametrize(
    "scenario_effect",
    (
        123,
        "effect",
        object(),
    ),
)
def test_scenario_generation_manifest_rejeita_scenario_effect_invalido(
    scenario_effect,
):
    from src.synthetic.generation_manifest import ScenarioGenerationManifest

    with pytest.raises(ValueError, match="scenario_effect"):
        ScenarioGenerationManifest(
            scenario="account_takeover",
            scenario_effect=scenario_effect,
        )


@pytest.mark.parametrize(
    "intensity_policy",
    (
        123,
        "policy",
        object(),
    ),
)
def test_scenario_generation_manifest_rejeita_intensity_policy_invalida(
    intensity_policy,
):
    from src.synthetic.generation_manifest import ScenarioGenerationManifest

    with pytest.raises(ValueError, match="intensity_policy"):
        ScenarioGenerationManifest(
            scenario="account_takeover",
            intensity_policy=intensity_policy,
        )


def test_scenario_generation_manifest_preserva_manifests_filhos():
    from src.synthetic.generation_manifest import (
        EventIntensityPolicyManifest,
        ScenarioEffectManifest,
        ScenarioGenerationManifest,
    )

    scenario_effect = ScenarioEffectManifest(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.1,
        recent_login_failure_rate_increment=0.35,
    )

    intensity_policy = EventIntensityPolicyManifest(
        intensity_min=0.2,
        intensity_max=0.8,
    )

    manifest = ScenarioGenerationManifest(
        scenario="account_takeover",
        scenario_effect=scenario_effect,
        intensity_policy=intensity_policy,
    )

    assert manifest.scenario_effect is scenario_effect
    assert manifest.intensity_policy is intensity_policy


def test_build_scenario_generation_manifest_cria_snapshot_composto():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.generation_manifest import (
        EventIntensityPolicyManifest,
        ScenarioEffectManifest,
    )
    from src.synthetic.generation_manifest_builder import (
        build_scenario_generation_manifest,
    )
    from src.synthetic.intensity import EventIntensityPolicy
    from src.synthetic.scenario_effects import ScenarioEffect

    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.1,
        recent_login_failure_rate_increment=0.35,
    )

    intensity_policy = EventIntensityPolicy(
        intensity_min=0.2,
        intensity_max=0.8,
    )

    config = ScenarioGenerationConfig(
        scenario="account_takeover",
        scenario_effect=effect,
        intensity_policy=intensity_policy,
    )

    manifest = build_scenario_generation_manifest(config)

    assert manifest.scenario == config.scenario

    assert isinstance(
        manifest.scenario_effect,
        ScenarioEffectManifest,
    )
    assert manifest.scenario_effect is not effect
    assert (
        manifest.scenario_effect.transaction_value_median_multiplier
        == effect.transaction_value_median_multiplier
    )
    assert (
        manifest.scenario_effect.transaction_value_sigma_multiplier
        == effect.transaction_value_sigma_multiplier
    )
    assert (
        manifest.scenario_effect.recent_login_failure_rate_increment
        == effect.recent_login_failure_rate_increment
    )

    assert isinstance(
        manifest.intensity_policy,
        EventIntensityPolicyManifest,
    )
    assert manifest.intensity_policy is not intensity_policy
    assert manifest.intensity_policy.intensity_min == intensity_policy.intensity_min
    assert manifest.intensity_policy.intensity_max == intensity_policy.intensity_max


@pytest.mark.parametrize(
    "config",
    (
        123,
        "scenario-config",
        object(),
        None,
    ),
)
def test_build_scenario_generation_manifest_rejeita_config_invalida(
    config,
):
    from src.synthetic.generation_manifest_builder import (
        build_scenario_generation_manifest,
    )

    with pytest.raises(ValueError, match="config"):
        build_scenario_generation_manifest(config)


def test_build_scenario_generation_manifest_preserva_componentes_opcionais_ausentes():
    from src.synthetic.generation_config import ScenarioGenerationConfig
    from src.synthetic.generation_manifest_builder import (
        build_scenario_generation_manifest,
    )

    config = ScenarioGenerationConfig(
        scenario="baseline",
    )

    manifest = build_scenario_generation_manifest(config)

    assert manifest.scenario == "baseline"
    assert manifest.scenario_effect is None
    assert manifest.intensity_policy is None


def test_scenario_generation_manifest_e_imutavel():
    from dataclasses import FrozenInstanceError

    from src.synthetic.generation_manifest import ScenarioGenerationManifest

    manifest = ScenarioGenerationManifest(
        scenario="account_takeover",
    )

    with pytest.raises(FrozenInstanceError):
        manifest.scenario = "baseline"
