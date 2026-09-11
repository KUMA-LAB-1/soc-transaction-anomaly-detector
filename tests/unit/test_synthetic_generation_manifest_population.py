import math
from dataclasses import FrozenInstanceError

import pytest


def test_behavior_flag_baseline_manifest_preserva_snapshot():
    from src.synthetic.generation_manifest import BehaviorFlagBaselineManifest

    manifest = BehaviorFlagBaselineManifest(
        new_device_probability=0.08,
        limit_change_probability=0.04,
        location_change_probability=0.07,
    )

    assert manifest.new_device_probability == 0.08
    assert manifest.limit_change_probability == 0.04
    assert manifest.location_change_probability == 0.07


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
        -0.01,
        1.01,
        math.nan,
        math.inf,
        -math.inf,
        True,
        None,
        "0.50",
    ),
)
def test_behavior_flag_baseline_manifest_rejeita_probabilidade_invalida(
    field_name,
    invalid_value,
):
    values = {
        "new_device_probability": 0.08,
        "limit_change_probability": 0.04,
        "location_change_probability": 0.07,
    }
    values[field_name] = invalid_value

    from src.synthetic.generation_manifest import BehaviorFlagBaselineManifest

    with pytest.raises(
        ValueError,
        match=field_name,
    ):
        BehaviorFlagBaselineManifest(**values)


def test_behavior_flag_baseline_manifest_aceita_limites_de_probabilidade():
    from src.synthetic.generation_manifest import BehaviorFlagBaselineManifest

    manifest = BehaviorFlagBaselineManifest(
        new_device_probability=0.0,
        limit_change_probability=1.0,
        location_change_probability=0.0,
    )

    assert manifest.new_device_probability == 0.0
    assert manifest.limit_change_probability == 1.0
    assert manifest.location_change_probability == 0.0


def test_population_generation_manifest_preserva_snapshot_da_configuracao():
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    manifest = PopulationGenerationManifest(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    assert manifest.customer_count == 100
    assert manifest.transaction_value_median_base == 180.0
    assert manifest.transaction_value_median_log_sigma == 0.75
    assert manifest.transaction_value_sigma == 0.65
    assert manifest.recent_login_failure_rate_mean == 0.15
    assert manifest.recent_login_failure_rate_shape == 2.0


def test_population_generation_manifest_preserva_behavior_flag_baseline():
    from src.synthetic.generation_manifest import (
        BehaviorFlagBaselineManifest,
        PopulationGenerationManifest,
    )

    behavior_flag_baseline = BehaviorFlagBaselineManifest(
        new_device_probability=0.08,
        limit_change_probability=0.04,
        location_change_probability=0.07,
    )

    manifest = PopulationGenerationManifest(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
        behavior_flag_baseline=behavior_flag_baseline,
    )

    assert manifest.behavior_flag_baseline is behavior_flag_baseline


def test_population_generation_manifest_mantem_behavior_flag_baseline_none_por_padrao():
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    manifest = PopulationGenerationManifest(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    assert manifest.behavior_flag_baseline is None


@pytest.mark.parametrize(
    "behavior_flag_baseline",
    (
        True,
        123,
        "baseline",
        {},
    ),
)
def test_population_generation_manifest_rejeita_behavior_flag_baseline_invalido(
    behavior_flag_baseline,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(
        ValueError,
        match="behavior_flag_baseline",
    ):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
            behavior_flag_baseline=behavior_flag_baseline,
        )


@pytest.mark.parametrize(
    "customer_count",
    (
        0,
        -1,
        True,
        1.5,
        "100",
        None,
    ),
)
def test_population_generation_manifest_rejeita_customer_count_invalido(
    customer_count,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="customer_count"):
        PopulationGenerationManifest(
            customer_count=customer_count,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "transaction_value_median_base",
    (
        0.0,
        -1.0,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "180.0",
        None,
    ),
)
def test_population_generation_manifest_rejeita_transaction_value_median_base_invalida(
    transaction_value_median_base,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="transaction_value_median_base"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=transaction_value_median_base,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "transaction_value_median_log_sigma",
    (
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "0.75",
        None,
    ),
)
def test_population_generation_manifest_rejeita_transaction_value_median_log_sigma_invalido(
    transaction_value_median_log_sigma,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="transaction_value_median_log_sigma"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=transaction_value_median_log_sigma,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "transaction_value_sigma",
    (
        0.0,
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "0.65",
        None,
    ),
)
def test_population_generation_manifest_rejeita_transaction_value_sigma_invalido(
    transaction_value_sigma,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="transaction_value_sigma"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=transaction_value_sigma,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "recent_login_failure_rate_mean",
    (
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "0.15",
        None,
    ),
)
def test_population_generation_manifest_rejeita_recent_login_failure_rate_mean_invalida(
    recent_login_failure_rate_mean,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="recent_login_failure_rate_mean"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=recent_login_failure_rate_mean,
            recent_login_failure_rate_shape=2.0,
        )


@pytest.mark.parametrize(
    "recent_login_failure_rate_shape",
    (
        0.0,
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "2.0",
        None,
    ),
)
def test_population_generation_manifest_rejeita_recent_login_failure_rate_shape_invalido(
    recent_login_failure_rate_shape,
):
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    with pytest.raises(ValueError, match="recent_login_failure_rate_shape"):
        PopulationGenerationManifest(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=recent_login_failure_rate_shape,
        )


def test_population_generation_manifest_aceita_limites_zero_permitidos():
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    manifest = PopulationGenerationManifest(
        customer_count=1,
        transaction_value_median_base=1.0,
        transaction_value_median_log_sigma=0.0,
        transaction_value_sigma=0.1,
        recent_login_failure_rate_mean=0.0,
        recent_login_failure_rate_shape=1.0,
    )

    assert manifest.transaction_value_median_log_sigma == 0.0
    assert manifest.recent_login_failure_rate_mean == 0.0


def test_population_generation_manifest_e_imutavel():
    from src.synthetic.generation_manifest import PopulationGenerationManifest

    manifest = PopulationGenerationManifest(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    with pytest.raises(FrozenInstanceError):
        manifest.customer_count = 200


def test_build_population_generation_manifest_cria_snapshot_da_configuracao():
    from src.synthetic.generation_manifest_builder import (
        build_population_generation_manifest,
    )
    from src.synthetic.population_generation import PopulationGenerationConfig

    config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    manifest = build_population_generation_manifest(config)

    assert manifest.customer_count == config.customer_count
    assert (
        manifest.transaction_value_median_base == config.transaction_value_median_base
    )
    assert (
        manifest.transaction_value_median_log_sigma
        == config.transaction_value_median_log_sigma
    )
    assert manifest.transaction_value_sigma == config.transaction_value_sigma
    assert (
        manifest.recent_login_failure_rate_mean == config.recent_login_failure_rate_mean
    )
    assert (
        manifest.recent_login_failure_rate_shape
        == config.recent_login_failure_rate_shape
    )
    assert manifest is not config


def test_build_population_generation_manifest_preserva_behavior_flag_baseline():
    from src.synthetic.behavior_flags import BehaviorFlagBaseline
    from src.synthetic.generation_manifest_builder import (
        build_population_generation_manifest,
    )
    from src.synthetic.population_generation import PopulationGenerationConfig

    behavior_flag_baseline = BehaviorFlagBaseline(
        new_device_probability=0.08,
        limit_change_probability=0.04,
        location_change_probability=0.07,
    )

    config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
        behavior_flag_baseline=behavior_flag_baseline,
    )

    manifest = build_population_generation_manifest(config)

    assert manifest.behavior_flag_baseline is not None
    assert (
        manifest.behavior_flag_baseline.new_device_probability
        == behavior_flag_baseline.new_device_probability
    )
    assert (
        manifest.behavior_flag_baseline.limit_change_probability
        == behavior_flag_baseline.limit_change_probability
    )
    assert (
        manifest.behavior_flag_baseline.location_change_probability
        == behavior_flag_baseline.location_change_probability
    )
    assert manifest.behavior_flag_baseline is not behavior_flag_baseline


@pytest.mark.parametrize(
    "config",
    (
        123,
        "population-config",
        object(),
        None,
    ),
)
def test_build_population_generation_manifest_rejeita_config_invalida(
    config,
):
    from src.synthetic.generation_manifest_builder import (
        build_population_generation_manifest,
    )

    with pytest.raises(ValueError, match="config"):
        build_population_generation_manifest(config)
