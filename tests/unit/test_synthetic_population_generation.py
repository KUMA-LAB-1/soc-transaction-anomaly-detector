from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.population_generation import PopulationGenerationConfig


def test_population_generation_config_preserva_parametros():
    config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    assert config.customer_count == 100
    assert config.transaction_value_median_base == 180.0
    assert config.transaction_value_median_log_sigma == 0.75
    assert config.transaction_value_sigma == 0.65
    assert config.recent_login_failure_rate_mean == 0.15
    assert config.recent_login_failure_rate_shape == 2.0


@pytest.mark.parametrize(
    "customer_count",
    (
        0,
        -1,
        True,
        1.5,
        None,
    ),
)
def test_population_generation_config_rejeita_customer_count_invalido(
    customer_count,
):
    with pytest.raises(
        ValueError,
        match="customer_count",
    ):
        PopulationGenerationConfig(
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
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        None,
        "180",
    ),
)
def test_population_generation_config_rejeita_mediana_base_invalida(
    transaction_value_median_base,
):
    with pytest.raises(
        ValueError,
        match="transaction_value_median_base",
    ):
        PopulationGenerationConfig(
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
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        None,
        "0.75",
    ),
)
def test_population_generation_config_rejeita_log_sigma_invalido(
    transaction_value_median_log_sigma,
):
    with pytest.raises(
        ValueError,
        match="transaction_value_median_log_sigma",
    ):
        PopulationGenerationConfig(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=transaction_value_median_log_sigma,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=2.0,
        )


def test_population_generation_config_aceita_log_sigma_zero():
    config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    assert config.transaction_value_median_log_sigma == 0.0


@pytest.mark.parametrize(
    "transaction_value_sigma",
    (
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        None,
        "0.65",
    ),
)
def test_population_generation_config_rejeita_transaction_sigma_invalido(
    transaction_value_sigma,
):
    with pytest.raises(
        ValueError,
        match="transaction_value_sigma",
    ):
        PopulationGenerationConfig(
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
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        None,
        "0.15",
    ),
)
def test_population_generation_config_rejeita_login_rate_mean_invalido(
    recent_login_failure_rate_mean,
):
    with pytest.raises(
        ValueError,
        match="recent_login_failure_rate_mean",
    ):
        PopulationGenerationConfig(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=recent_login_failure_rate_mean,
            recent_login_failure_rate_shape=2.0,
        )


def test_population_generation_config_aceita_login_rate_mean_zero():
    config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.0,
        recent_login_failure_rate_shape=2.0,
    )

    assert config.recent_login_failure_rate_mean == 0.0


@pytest.mark.parametrize(
    "recent_login_failure_rate_shape",
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
def test_population_generation_config_rejeita_login_rate_shape_invalido(
    recent_login_failure_rate_shape,
):
    with pytest.raises(
        ValueError,
        match="recent_login_failure_rate_shape",
    ):
        PopulationGenerationConfig(
            customer_count=100,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.75,
            transaction_value_sigma=0.65,
            recent_login_failure_rate_mean=0.15,
            recent_login_failure_rate_shape=recent_login_failure_rate_shape,
        )


def test_population_generation_config_e_imutavel():
    config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    with pytest.raises(FrozenInstanceError):
        config.customer_count = 200
