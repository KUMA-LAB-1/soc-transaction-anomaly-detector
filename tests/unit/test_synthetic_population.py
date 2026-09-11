from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.behavior_flags import BehaviorFlagBaseline
from src.synthetic.population import (
    CustomerBehaviorProfile,
    CustomerPopulation,
)


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


def test_customer_behavior_profile_preserva_behavior_flag_baseline():
    behavior_flag_baseline = BehaviorFlagBaseline(
        new_device_probability=0.08,
        limit_change_probability=0.04,
        location_change_probability=0.07,
    )

    profile = CustomerBehaviorProfile(
        customer_pseudonym="cliente-042",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.15,
        behavior_flag_baseline=behavior_flag_baseline,
    )

    assert profile.behavior_flag_baseline is behavior_flag_baseline


def test_customer_behavior_profile_mantem_behavior_flag_baseline_none_por_padrao():
    profile = CustomerBehaviorProfile(
        customer_pseudonym="cliente-042",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.15,
    )

    assert profile.behavior_flag_baseline is None


@pytest.mark.parametrize(
    "behavior_flag_baseline",
    (
        True,
        123,
        "baseline",
        {},
    ),
)
def test_customer_behavior_profile_rejeita_behavior_flag_baseline_invalido(
    behavior_flag_baseline,
):
    with pytest.raises(
        ValueError,
        match="behavior_flag_baseline",
    ):
        CustomerBehaviorProfile(
            customer_pseudonym="cliente-042",
            transaction_value_median=180.0,
            transaction_value_sigma=0.65,
            recent_login_failure_rate=0.15,
            behavior_flag_baseline=behavior_flag_baseline,
        )


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


def _build_customer_profile(
    customer_pseudonym: str,
    *,
    transaction_value_median: float = 180.0,
    transaction_value_sigma: float = 0.65,
    recent_login_failure_rate: float = 0.15,
) -> CustomerBehaviorProfile:
    return CustomerBehaviorProfile(
        customer_pseudonym=customer_pseudonym,
        transaction_value_median=transaction_value_median,
        transaction_value_sigma=transaction_value_sigma,
        recent_login_failure_rate=recent_login_failure_rate,
    )


def test_customer_population_preserva_ordem_dos_profiles():
    primeiro = _build_customer_profile("cliente-001")
    segundo = _build_customer_profile(
        "cliente-002",
        transaction_value_median=450.0,
    )

    population = CustomerPopulation(
        profiles=(
            primeiro,
            segundo,
        )
    )

    assert population.profiles == (
        primeiro,
        segundo,
    )


def test_customer_population_rejeita_populacao_vazia():
    with pytest.raises(
        ValueError,
        match="profiles",
    ):
        CustomerPopulation(
            profiles=(),
        )


def test_customer_population_rejeita_profiles_fora_de_tuple():
    with pytest.raises(
        ValueError,
        match="profiles",
    ):
        CustomerPopulation(
            profiles=[],
        )


def test_customer_population_rejeita_elemento_invalido():
    profile = _build_customer_profile("cliente-001")

    with pytest.raises(
        ValueError,
        match="CustomerBehaviorProfile",
    ):
        CustomerPopulation(
            profiles=(
                profile,
                "cliente-002",
            ),
        )


def test_customer_population_rejeita_customer_pseudonym_duplicado():
    primeiro = _build_customer_profile("cliente-001")
    duplicado = _build_customer_profile(
        "cliente-001",
        transaction_value_median=900.0,
    )

    with pytest.raises(
        ValueError,
        match="customer_pseudonym",
    ):
        CustomerPopulation(
            profiles=(
                primeiro,
                duplicado,
            ),
        )


def test_customer_population_retorna_profile_por_pseudonimo():
    primeiro = _build_customer_profile("cliente-001")
    segundo = _build_customer_profile(
        "cliente-002",
        transaction_value_median=450.0,
    )

    population = CustomerPopulation(
        profiles=(
            primeiro,
            segundo,
        )
    )

    assert population.get_profile("cliente-002") is segundo


def test_customer_population_rejeita_lookup_desconhecido():
    population = CustomerPopulation(profiles=(_build_customer_profile("cliente-001"),))

    with pytest.raises(
        ValueError,
        match="cliente-999",
    ):
        population.get_profile("cliente-999")


def test_customer_population_e_imutavel():
    population = CustomerPopulation(profiles=(_build_customer_profile("cliente-001"),))

    with pytest.raises(FrozenInstanceError):
        population.profiles = ()
