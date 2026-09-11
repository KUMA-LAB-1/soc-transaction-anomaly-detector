from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.behavior_flags import BehaviorFlagBaseline


def _build_behavior_flag_baseline(
    **overrides,
) -> BehaviorFlagBaseline:
    values = {
        "new_device_probability": 0.08,
        "limit_change_probability": 0.04,
        "location_change_probability": 0.07,
    }
    values.update(overrides)

    return BehaviorFlagBaseline(**values)


def test_behavior_flag_baseline_preserva_probabilidades():
    baseline = _build_behavior_flag_baseline()

    assert baseline.new_device_probability == 0.08
    assert baseline.limit_change_probability == 0.04
    assert baseline.location_change_probability == 0.07


@pytest.mark.parametrize(
    "field_name",
    (
        "new_device_probability",
        "limit_change_probability",
        "location_change_probability",
    ),
)
@pytest.mark.parametrize(
    "invalid_value",
    (
        -0.1,
        1.1,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        None,
        "0.50",
    ),
)
def test_behavior_flag_baseline_rejeita_probabilidade_invalida(
    field_name,
    invalid_value,
):
    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        _build_behavior_flag_baseline(
            **{field_name: invalid_value},
        )


@pytest.mark.parametrize(
    "boundary_value",
    (
        0.0,
        1.0,
    ),
)
def test_behavior_flag_baseline_aceita_limites_inclusivos(
    boundary_value,
):
    baseline = BehaviorFlagBaseline(
        new_device_probability=boundary_value,
        limit_change_probability=boundary_value,
        location_change_probability=boundary_value,
    )

    assert baseline.new_device_probability == boundary_value
    assert baseline.limit_change_probability == boundary_value
    assert baseline.location_change_probability == boundary_value


def test_behavior_flag_baseline_e_imutavel():
    baseline = _build_behavior_flag_baseline()

    with pytest.raises(FrozenInstanceError):
        baseline.new_device_probability = 0.50
