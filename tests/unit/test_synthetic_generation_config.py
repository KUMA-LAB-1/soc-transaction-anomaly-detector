from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.intensity import EventIntensityPolicy
from src.synthetic.population_generation import PopulationGenerationConfig
from src.synthetic.scenario_effects import ScenarioEffect
from src.synthetic.severity import SeverityPolicy


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


def test_synthetic_generation_config_preserva_componentes_globais_e_por_cenario():
    from src.synthetic.generation_config import (
        ScenarioGenerationConfig,
        SyntheticGenerationConfig,
    )

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

    scenario_config = ScenarioGenerationConfig(
        scenario="account_takeover",
    )

    config = SyntheticGenerationConfig(
        population_config=population_config,
        severity_policy=severity_policy,
        scenario_configs=(scenario_config,),
    )

    assert config.population_config is population_config
    assert config.severity_policy is severity_policy
    assert config.scenario_configs == (scenario_config,)


def test_synthetic_generation_config_aceita_componentes_opcionais():
    from src.synthetic.generation_config import SyntheticGenerationConfig

    config = SyntheticGenerationConfig()

    assert config.population_config is None
    assert config.severity_policy is None
    assert config.scenario_configs == ()


@pytest.mark.parametrize(
    "population_config",
    (
        123,
        "population",
        object(),
    ),
)
def test_synthetic_generation_config_rejeita_population_config_invalida(
    population_config,
):
    from src.synthetic.generation_config import SyntheticGenerationConfig

    with pytest.raises(ValueError, match="population_config"):
        SyntheticGenerationConfig(
            population_config=population_config,
        )


@pytest.mark.parametrize(
    "severity_policy",
    (
        123,
        "severity",
        object(),
    ),
)
def test_synthetic_generation_config_rejeita_severity_policy_invalida(
    severity_policy,
):
    from src.synthetic.generation_config import SyntheticGenerationConfig

    with pytest.raises(ValueError, match="severity_policy"):
        SyntheticGenerationConfig(
            severity_policy=severity_policy,
        )


@pytest.mark.parametrize(
    "scenario_configs",
    (
        [],
        ["account_takeover"],
        "account_takeover",
        None,
    ),
)
def test_synthetic_generation_config_rejeita_scenario_configs_que_nao_sao_tuple(
    scenario_configs,
):
    from src.synthetic.generation_config import SyntheticGenerationConfig

    with pytest.raises(ValueError, match="scenario_configs"):
        SyntheticGenerationConfig(
            scenario_configs=scenario_configs,
        )


@pytest.mark.parametrize(
    "scenario_config",
    (
        123,
        "account_takeover",
        object(),
        None,
    ),
)
def test_synthetic_generation_config_rejeita_item_invalido_em_scenario_configs(
    scenario_config,
):
    from src.synthetic.generation_config import SyntheticGenerationConfig

    with pytest.raises(ValueError, match="scenario_configs"):
        SyntheticGenerationConfig(
            scenario_configs=(scenario_config,),
        )


def test_synthetic_generation_config_rejeita_scenario_configs_duplicados():
    from src.synthetic.generation_config import (
        ScenarioGenerationConfig,
        SyntheticGenerationConfig,
    )

    primeiro = ScenarioGenerationConfig(
        scenario="account_takeover",
        scenario_effect=ScenarioEffect(
            transaction_value_median_multiplier=1.5,
            transaction_value_sigma_multiplier=1.10,
            recent_login_failure_rate_increment=0.35,
        ),
    )

    segundo = ScenarioGenerationConfig(
        scenario="account_takeover",
        intensity_policy=EventIntensityPolicy(
            intensity_min=0.20,
            intensity_max=0.80,
        ),
    )

    with pytest.raises(ValueError, match="scenario_configs"):
        SyntheticGenerationConfig(
            scenario_configs=(
                primeiro,
                segundo,
            ),
        )


def test_synthetic_generation_config_e_imutavel():
    from src.synthetic.generation_config import SyntheticGenerationConfig

    config = SyntheticGenerationConfig()

    with pytest.raises(FrozenInstanceError):
        config.scenario_configs = ()


def test_synthetic_generation_config_aceita_scenario_configs_distintos():
    from src.synthetic.generation_config import (
        ScenarioGenerationConfig,
        SyntheticGenerationConfig,
    )

    account_takeover = ScenarioGenerationConfig(
        scenario="account_takeover",
    )

    credential_attack = ScenarioGenerationConfig(
        scenario="credential_attack",
    )

    config = SyntheticGenerationConfig(
        scenario_configs=(
            account_takeover,
            credential_attack,
        ),
    )

    assert config.scenario_configs == (
        account_takeover,
        credential_attack,
    )


@pytest.mark.parametrize(
    "scenario",
    (
        " account_takeover",
        "account_takeover ",
        "\taccount_takeover",
        "account_takeover\n",
    ),
)
def test_scenario_generation_config_rejeita_scenario_com_whitespace_externo(
    scenario,
):
    from src.synthetic.generation_config import ScenarioGenerationConfig

    with pytest.raises(ValueError, match="scenario"):
        ScenarioGenerationConfig(
            scenario=scenario,
        )
