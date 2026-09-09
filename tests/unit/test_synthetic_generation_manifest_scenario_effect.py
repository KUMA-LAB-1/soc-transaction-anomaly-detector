import math
from dataclasses import FrozenInstanceError

import pytest


def test_scenario_effect_manifest_preserva_snapshot_do_efeito():
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    manifest = ScenarioEffectManifest(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.1,
        recent_login_failure_rate_increment=0.35,
    )

    assert manifest.transaction_value_median_multiplier == 1.5
    assert manifest.transaction_value_sigma_multiplier == 1.1
    assert manifest.recent_login_failure_rate_increment == 0.35


@pytest.mark.parametrize(
    "valor_invalido",
    (
        0.0,
        -1.0,
        math.nan,
        math.inf,
        -math.inf,
        True,
        None,
        "2.0",
    ),
)
def test_scenario_effect_manifest_rejeita_multiplicador_de_mediana_invalido(
    valor_invalido,
):
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    with pytest.raises(
        ValueError,
        match="transaction_value_median_multiplier",
    ):
        ScenarioEffectManifest(
            transaction_value_median_multiplier=valor_invalido,
            transaction_value_sigma_multiplier=1.0,
            recent_login_failure_rate_increment=0.0,
        )


@pytest.mark.parametrize(
    "valor_invalido",
    (
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        None,
        "1.0",
    ),
)
def test_scenario_effect_manifest_rejeita_multiplicador_de_sigma_invalido(
    valor_invalido,
):
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    with pytest.raises(
        ValueError,
        match="transaction_value_sigma_multiplier",
    ):
        ScenarioEffectManifest(
            transaction_value_median_multiplier=1.0,
            transaction_value_sigma_multiplier=valor_invalido,
            recent_login_failure_rate_increment=0.0,
        )


@pytest.mark.parametrize(
    "valor_invalido",
    (
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        None,
        "1.0",
    ),
)
def test_scenario_effect_manifest_rejeita_incremento_de_login_invalido(
    valor_invalido,
):
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    with pytest.raises(
        ValueError,
        match="recent_login_failure_rate_increment",
    ):
        ScenarioEffectManifest(
            transaction_value_median_multiplier=1.0,
            transaction_value_sigma_multiplier=1.0,
            recent_login_failure_rate_increment=valor_invalido,
        )


def test_scenario_effect_manifest_aceita_sigma_e_incremento_de_login_zero():
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    manifest = ScenarioEffectManifest(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=0.0,
        recent_login_failure_rate_increment=0.0,
    )

    assert manifest.transaction_value_sigma_multiplier == 0.0
    assert manifest.recent_login_failure_rate_increment == 0.0


def test_scenario_effect_manifest_e_imutavel():
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    manifest = ScenarioEffectManifest(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.1,
        recent_login_failure_rate_increment=0.35,
    )

    with pytest.raises(FrozenInstanceError):
        manifest.transaction_value_median_multiplier = 2.0


def test_build_scenario_effect_manifest_cria_snapshot_do_efeito():
    from src.synthetic.generation_manifest_builder import (
        build_scenario_effect_manifest,
    )
    from src.synthetic.scenario_effects import ScenarioEffect

    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.1,
        recent_login_failure_rate_increment=0.35,
    )

    manifest = build_scenario_effect_manifest(effect)

    assert (
        manifest.transaction_value_median_multiplier
        == effect.transaction_value_median_multiplier
    )
    assert (
        manifest.transaction_value_sigma_multiplier
        == effect.transaction_value_sigma_multiplier
    )
    assert (
        manifest.recent_login_failure_rate_increment
        == effect.recent_login_failure_rate_increment
    )
    assert manifest is not effect


@pytest.mark.parametrize(
    "effect",
    (
        123,
        "scenario-effect",
        object(),
        None,
    ),
)
def test_build_scenario_effect_manifest_rejeita_effect_invalido(
    effect,
):
    from src.synthetic.generation_manifest_builder import (
        build_scenario_effect_manifest,
    )

    with pytest.raises(ValueError, match="effect"):
        build_scenario_effect_manifest(effect)
