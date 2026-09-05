from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.population import CustomerBehaviorProfile


def test_customer_behavior_profile_preserva_baseline_do_cliente():
    profile = CustomerBehaviorProfile(
        customer_pseudonym="cliente-042",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.15,
    )

    assert profile.customer_pseudonym == "cliente-042"
    assert profile.transaction_value_median == 180.0
    assert profile.transaction_value_sigma == 0.65
    assert profile.recent_login_failure_rate == 0.15


@pytest.mark.parametrize(
    "customer_pseudonym",
    (
        "",
        "   ",
        None,
        123,
    ),
)
def test_customer_behavior_profile_rejeita_identificador_invalido(
    customer_pseudonym,
):
    with pytest.raises(
        ValueError,
        match="customer_pseudonym",
    ):
        CustomerBehaviorProfile(
            customer_pseudonym=customer_pseudonym,
            transaction_value_median=180.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate=0.15,
        )


@pytest.mark.parametrize(
    "transaction_value_median",
    (
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        None,
        "180",
    ),
)
def test_customer_behavior_profile_rejeita_mediana_invalida(
    transaction_value_median,
):
    with pytest.raises(
        ValueError,
        match="transaction_value_median",
    ):
        CustomerBehaviorProfile(
            customer_pseudonym="cliente-001",
            transaction_value_median=transaction_value_median,
            transaction_value_sigma=0.65,
            recent_login_failure_rate=0.15,
        )


@pytest.mark.parametrize(
    "transaction_value_sigma",
    (
        0.0,
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        None,
        "0.65",
    ),
)
def test_customer_behavior_profile_rejeita_sigma_invalido(
    transaction_value_sigma,
):
    with pytest.raises(
        ValueError,
        match="transaction_value_sigma",
    ):
        CustomerBehaviorProfile(
            customer_pseudonym="cliente-001",
            transaction_value_median=180.0,
            transaction_value_sigma=transaction_value_sigma,
            recent_login_failure_rate=0.15,
        )


@pytest.mark.parametrize(
    "recent_login_failure_rate",
    (
        -1.0,
        float("nan"),
        float("inf"),
        float("-inf"),
        None,
        "0.15",
    ),
)
def test_customer_behavior_profile_rejeita_taxa_login_invalida(
    recent_login_failure_rate,
):
    with pytest.raises(
        ValueError,
        match="recent_login_failure_rate",
    ):
        CustomerBehaviorProfile(
            customer_pseudonym="cliente-001",
            transaction_value_median=180.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate=recent_login_failure_rate,
        )


def test_customer_behavior_profile_e_imutavel():
    profile = CustomerBehaviorProfile(
        customer_pseudonym="cliente-001",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.15,
    )

    with pytest.raises(FrozenInstanceError):
        profile.transaction_value_median = 500.0


def test_customer_behavior_profile_rejeita_bool_como_mediana():
    with pytest.raises(
        ValueError,
        match="transaction_value_median",
    ):
        CustomerBehaviorProfile(
            customer_pseudonym="cliente-001",
            transaction_value_median=True,
            transaction_value_sigma=0.65,
            recent_login_failure_rate=0.15,
        )


def test_customer_behavior_profile_rejeita_bool_como_sigma():
    with pytest.raises(
        ValueError,
        match="transaction_value_sigma",
    ):
        CustomerBehaviorProfile(
            customer_pseudonym="cliente-001",
            transaction_value_median=180.0,
            transaction_value_sigma=True,
            recent_login_failure_rate=0.15,
        )


def test_customer_behavior_profile_rejeita_bool_como_taxa_login():
    with pytest.raises(
        ValueError,
        match="recent_login_failure_rate",
    ):
        CustomerBehaviorProfile(
            customer_pseudonym="cliente-001",
            transaction_value_median=180.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate=True,
        )
