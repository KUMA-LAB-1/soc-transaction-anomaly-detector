from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.intensity import EventIntensityPolicy
from src.synthetic.scenario_effects import ScenarioEffect


def test_scenario_generation_config_preserva_configuracao_do_cenario():
    from src.synthetic.generation_config import ScenarioGenerationConfig

    scenario_effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.10,
        recent_login_failure_rate_increment=0.35,
    )

    intensity_policy = EventIntensityPolicy(
        intensity_min=0.20,
        intensity_max=0.80,
    )

    config = ScenarioGenerationConfig(
        scenario="account_takeover",
        scenario_effect=scenario_effect,
        intensity_policy=intensity_policy,
    )

    assert config.scenario == "account_takeover"
    assert config.scenario_effect is scenario_effect
    assert config.intensity_policy is intensity_policy


@pytest.mark.parametrize(
    "scenario",
    (
        "",
        "   ",
        None,
        123,
    ),
)
def test_scenario_generation_config_rejeita_scenario_invalido(scenario):
    from src.synthetic.generation_config import ScenarioGenerationConfig

    with pytest.raises(ValueError, match="scenario"):
        ScenarioGenerationConfig(
            scenario=scenario,
            scenario_effect=ScenarioEffect(
                transaction_value_median_multiplier=1.0,
                transaction_value_sigma_multiplier=1.0,
                recent_login_failure_rate_increment=0.0,
            ),
            intensity_policy=EventIntensityPolicy(
                intensity_min=0.0,
                intensity_max=1.0,
            ),
        )


def test_scenario_generation_config_aceita_componentes_opcionais():
    from src.synthetic.generation_config import ScenarioGenerationConfig

    config = ScenarioGenerationConfig(
        scenario="baseline",
    )

    assert config.scenario_effect is None
    assert config.intensity_policy is None


@pytest.mark.parametrize(
    "scenario_effect",
    (
        123,
        "effect",
        object(),
    ),
)
def test_scenario_generation_config_rejeita_scenario_effect_invalido(
    scenario_effect,
):
    from src.synthetic.generation_config import ScenarioGenerationConfig

    with pytest.raises(ValueError, match="scenario_effect"):
        ScenarioGenerationConfig(
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
def test_scenario_generation_config_rejeita_intensity_policy_invalida(
    intensity_policy,
):
    from src.synthetic.generation_config import ScenarioGenerationConfig

    with pytest.raises(ValueError, match="intensity_policy"):
        ScenarioGenerationConfig(
            scenario="account_takeover",
            intensity_policy=intensity_policy,
        )


def test_scenario_generation_config_e_imutavel():
    from src.synthetic.generation_config import ScenarioGenerationConfig

    config = ScenarioGenerationConfig(
        scenario="account_takeover",
    )

    with pytest.raises(FrozenInstanceError):
        config.scenario = "baseline"
