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


def test_scenario_effect_manifest_preserva_deltas_booleanos():
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    manifest = ScenarioEffectManifest(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.1,
        recent_login_failure_rate_increment=0.35,
        new_device_probability_delta=0.40,
        limit_change_probability_delta=-0.20,
        location_change_probability_delta=0.30,
    )

    assert manifest.new_device_probability_delta == 0.40
    assert manifest.limit_change_probability_delta == -0.20
    assert manifest.location_change_probability_delta == 0.30


def test_scenario_effect_manifest_mantem_deltas_booleanos_neutros_por_padrao():
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    manifest = ScenarioEffectManifest(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    )

    assert manifest.new_device_probability_delta == 0.0
    assert manifest.limit_change_probability_delta == 0.0
    assert manifest.location_change_probability_delta == 0.0


@pytest.mark.parametrize(
    "field_name",
    (
        "new_device_probability_delta",
        "limit_change_probability_delta",
        "location_change_probability_delta",
    ),
)
@pytest.mark.parametrize(
    "invalid_value",
    (
        -1.01,
        1.01,
        math.nan,
        math.inf,
        -math.inf,
        True,
        None,
        "0.25",
    ),
)
def test_scenario_effect_manifest_rejeita_delta_booleano_invalido(
    field_name,
    invalid_value,
):
    values = {
        "transaction_value_median_multiplier": 1.0,
        "transaction_value_sigma_multiplier": 1.0,
        "recent_login_failure_rate_increment": 0.0,
        "new_device_probability_delta": 0.0,
        "limit_change_probability_delta": 0.0,
        "location_change_probability_delta": 0.0,
    }
    values[field_name] = invalid_value

    from src.synthetic.generation_manifest import ScenarioEffectManifest

    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        ScenarioEffectManifest(**values)


def test_scenario_effect_manifest_aceita_limites_dos_deltas_booleanos():
    from src.synthetic.generation_manifest import ScenarioEffectManifest

    manifest = ScenarioEffectManifest(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
        new_device_probability_delta=-1.0,
        limit_change_probability_delta=1.0,
        location_change_probability_delta=-1.0,
    )

    assert manifest.new_device_probability_delta == -1.0
    assert manifest.limit_change_probability_delta == 1.0
    assert manifest.location_change_probability_delta == -1.0


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


def test_build_scenario_effect_manifest_preserva_deltas_booleanos():
    from src.synthetic.generation_manifest_builder import (
        build_scenario_effect_manifest,
    )
    from src.synthetic.scenario_effects import ScenarioEffect

    effect = ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.1,
        recent_login_failure_rate_increment=0.35,
        new_device_probability_delta=0.40,
        limit_change_probability_delta=-0.20,
        location_change_probability_delta=0.30,
    )

    manifest = build_scenario_effect_manifest(effect)

    assert manifest.new_device_probability_delta == effect.new_device_probability_delta
    assert (
        manifest.limit_change_probability_delta == effect.limit_change_probability_delta
    )
    assert (
        manifest.location_change_probability_delta
        == effect.location_change_probability_delta
    )


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
