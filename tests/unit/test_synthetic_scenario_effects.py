from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.scenario_effects import ScenarioEffect


def test_scenario_effect_preserva_parametros():
    effect = ScenarioEffect(
        transaction_value_median_multiplier=2.5,
        transaction_value_sigma_multiplier=1.2,
        recent_login_failure_rate_increment=3.0,
    )

    assert effect.transaction_value_median_multiplier == 2.5
    assert effect.transaction_value_sigma_multiplier == 1.2
    assert effect.recent_login_failure_rate_increment == 3.0


@pytest.mark.parametrize(
    "transaction_value_median_multiplier",
    (
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        None,
        "2.0",
    ),
)
def test_scenario_effect_rejeita_multiplicador_de_mediana_invalido(
    transaction_value_median_multiplier,
):
    with pytest.raises(
        ValueError,
        match="transaction_value_median_multiplier",
    ):
        ScenarioEffect(
            transaction_value_median_multiplier=transaction_value_median_multiplier,
            transaction_value_sigma_multiplier=1.0,
            recent_login_failure_rate_increment=0.0,
        )


@pytest.mark.parametrize(
    "transaction_value_sigma_multiplier",
    (
        -0.1,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        None,
        "1.0",
    ),
)
def test_scenario_effect_rejeita_multiplicador_de_sigma_invalido(
    transaction_value_sigma_multiplier,
):
    with pytest.raises(
        ValueError,
        match="transaction_value_sigma_multiplier",
    ):
        ScenarioEffect(
            transaction_value_median_multiplier=1.0,
            transaction_value_sigma_multiplier=transaction_value_sigma_multiplier,
            recent_login_failure_rate_increment=0.0,
        )


def test_scenario_effect_aceita_multiplicador_de_sigma_zero():
    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=0.0,
        recent_login_failure_rate_increment=0.0,
    )

    assert effect.transaction_value_sigma_multiplier == 0.0


@pytest.mark.parametrize(
    "recent_login_failure_rate_increment",
    (
        -0.1,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        None,
        "1.0",
    ),
)
def test_scenario_effect_rejeita_incremento_de_login_invalido(
    recent_login_failure_rate_increment,
):
    with pytest.raises(
        ValueError,
        match="recent_login_failure_rate_increment",
    ):
        ScenarioEffect(
            transaction_value_median_multiplier=1.0,
            transaction_value_sigma_multiplier=1.0,
            recent_login_failure_rate_increment=recent_login_failure_rate_increment,
        )


def test_scenario_effect_aceita_incremento_de_login_zero():
    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )

    assert effect.recent_login_failure_rate_increment == 0.0


def test_scenario_effect_e_imutavel():
    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )

    with pytest.raises(FrozenInstanceError):
        effect.transaction_value_median_multiplier = 2.0


def test_scenario_effect_intensidade_zero_retorna_efeito_neutro():
    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.10,
        recent_login_failure_rate_increment=0.35,
    )

    resultado = effect.aplicar_intensidade(0.0)

    assert resultado == ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )


def test_scenario_effect_intensidade_intermediaria_interpola_efeito():
    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.10,
        recent_login_failure_rate_increment=0.35,
    )

    resultado = effect.aplicar_intensidade(0.5)

    assert resultado.transaction_value_median_multiplier == pytest.approx(1.25)
    assert resultado.transaction_value_sigma_multiplier == pytest.approx(1.05)
    assert resultado.recent_login_failure_rate_increment == pytest.approx(0.175)


def test_scenario_effect_intensidade_um_preserva_efeito_original():
    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.10,
        recent_login_failure_rate_increment=0.35,
    )

    resultado = effect.aplicar_intensidade(1.0)

    assert resultado == effect


@pytest.mark.parametrize(
    "intensidade",
    [
        -0.01,
        1.01,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        "0.5",
        None,
    ],
)
def test_scenario_effect_rejeita_intensidade_invalida(intensidade):
    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.10,
        recent_login_failure_rate_increment=0.35,
    )

    with pytest.raises(
        ValueError,
        match="intensidade",
    ):
        effect.aplicar_intensidade(intensidade)
