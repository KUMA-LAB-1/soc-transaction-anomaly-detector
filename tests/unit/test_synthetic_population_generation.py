from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.behavior_flags import BehaviorFlagBaseline
from src.synthetic.population import CustomerPopulation
from src.synthetic.population_generation import (
    PopulationGenerationConfig,
    PopulationGenerator,
)


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


def test_population_generation_config_preserva_behavior_flag_baseline():
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

    assert config.behavior_flag_baseline is behavior_flag_baseline


def test_population_generation_config_mantem_behavior_flag_baseline_none_por_padrao():
    config = PopulationGenerationConfig(
        customer_count=100,
        transaction_value_median_base=180.0,
        transaction_value_median_log_sigma=0.75,
        transaction_value_sigma=0.65,
        recent_login_failure_rate_mean=0.15,
        recent_login_failure_rate_shape=2.0,
    )

    assert config.behavior_flag_baseline is None


@pytest.mark.parametrize(
    "behavior_flag_baseline",
    (
        True,
        123,
        "baseline",
        {},
    ),
)
def test_population_generation_config_rejeita_behavior_flag_baseline_invalido(
    behavior_flag_baseline,
):
    with pytest.raises(
        ValueError,
        match="behavior_flag_baseline",
    ):
        PopulationGenerationConfig(
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


def _build_population_generation_config(
    *,
    customer_count: int = 10,
    transaction_value_median_base: float = 180.0,
    transaction_value_median_log_sigma: float = 0.75,
    transaction_value_sigma: float = 0.65,
    recent_login_failure_rate_mean: float = 0.15,
    recent_login_failure_rate_shape: float = 2.0,
    behavior_flag_baseline: BehaviorFlagBaseline | None = None,
) -> PopulationGenerationConfig:
    return PopulationGenerationConfig(
        customer_count=customer_count,
        transaction_value_median_base=transaction_value_median_base,
        transaction_value_median_log_sigma=transaction_value_median_log_sigma,
        transaction_value_sigma=transaction_value_sigma,
        recent_login_failure_rate_mean=recent_login_failure_rate_mean,
        recent_login_failure_rate_shape=recent_login_failure_rate_shape,
        behavior_flag_baseline=behavior_flag_baseline,
    )


def test_population_generator_propaga_behavior_flag_baseline_para_perfis():
    behavior_flag_baseline = BehaviorFlagBaseline(
        new_device_probability=0.08,
        limit_change_probability=0.04,
        location_change_probability=0.07,
    )
    generator = PopulationGenerator(seed=42)

    population = generator.generate(
        _build_population_generation_config(
            customer_count=5,
            behavior_flag_baseline=behavior_flag_baseline,
        )
    )

    assert all(
        profile.behavior_flag_baseline is behavior_flag_baseline
        for profile in population.profiles
    )


def test_population_generator_retorna_customer_population():
    generator = PopulationGenerator(seed=42)

    population = generator.generate(
        _build_population_generation_config(),
    )

    assert isinstance(population, CustomerPopulation)


def test_population_generator_gera_quantidade_e_pseudonimos_estaveis():
    generator = PopulationGenerator(seed=42)

    population = generator.generate(
        _build_population_generation_config(
            customer_count=3,
        )
    )

    assert len(population.profiles) == 3
    assert tuple(profile.customer_pseudonym for profile in population.profiles) == (
        "cliente-001",
        "cliente-002",
        "cliente-003",
    )


def test_population_generator_preserva_sigma_transacional_configurado():
    generator = PopulationGenerator(seed=42)

    population = generator.generate(
        _build_population_generation_config(
            customer_count=10,
            transaction_value_sigma=0.82,
        )
    )

    assert all(
        profile.transaction_value_sigma == 0.82 for profile in population.profiles
    )


def test_population_generator_gera_baselines_validos():
    generator = PopulationGenerator(seed=42)

    population = generator.generate(
        _build_population_generation_config(
            customer_count=100,
        )
    )

    assert all(profile.transaction_value_median > 0 for profile in population.profiles)
    assert all(
        profile.recent_login_failure_rate >= 0 for profile in population.profiles
    )


def test_population_generator_behavior_flag_baseline_nao_altera_streams_existentes():
    behavior_flag_baseline = BehaviorFlagBaseline(
        new_device_probability=0.08,
        limit_change_probability=0.04,
        location_change_probability=0.07,
    )

    sem_behavior_flags = PopulationGenerator(seed=2026).generate(
        _build_population_generation_config(
            customer_count=25,
        )
    )

    com_behavior_flags = PopulationGenerator(seed=2026).generate(
        _build_population_generation_config(
            customer_count=25,
            behavior_flag_baseline=behavior_flag_baseline,
        )
    )

    assert tuple(
        profile.transaction_value_median for profile in sem_behavior_flags.profiles
    ) == tuple(
        profile.transaction_value_median for profile in com_behavior_flags.profiles
    )

    assert tuple(
        profile.recent_login_failure_rate for profile in sem_behavior_flags.profiles
    ) == tuple(
        profile.recent_login_failure_rate for profile in com_behavior_flags.profiles
    )


def test_population_generator_e_reprodutivel_na_mesma_instancia():
    generator = PopulationGenerator(seed=2026)
    config = _build_population_generation_config(
        customer_count=25,
    )

    primeira = generator.generate(config)
    segunda = generator.generate(config)

    assert primeira == segunda


def test_population_generator_e_reprodutivel_entre_instancias():
    config = _build_population_generation_config(
        customer_count=25,
    )

    primeira = PopulationGenerator(
        seed=2026,
    ).generate(config)

    segunda = PopulationGenerator(
        seed=2026,
    ).generate(config)

    assert primeira == segunda


def test_population_generator_seed_diferente_altera_populacao_estocastica():
    config = _build_population_generation_config(
        customer_count=25,
        transaction_value_median_log_sigma=0.75,
        recent_login_failure_rate_mean=0.15,
    )

    primeira = PopulationGenerator(
        seed=41,
    ).generate(config)

    segunda = PopulationGenerator(
        seed=42,
    ).generate(config)

    assert primeira != segunda


def test_population_generator_controles_sem_heterogeneidade():
    generator = PopulationGenerator(seed=42)

    population = generator.generate(
        _build_population_generation_config(
            customer_count=5,
            transaction_value_median_base=180.0,
            transaction_value_median_log_sigma=0.0,
            recent_login_failure_rate_mean=0.0,
        )
    )

    assert all(
        profile.transaction_value_median == 180.0 for profile in population.profiles
    )
    assert all(
        profile.recent_login_failure_rate == 0.0 for profile in population.profiles
    )


@pytest.mark.parametrize(
    "seed",
    (
        -1,
        True,
        1.5,
        None,
        "42",
    ),
)
def test_population_generator_rejeita_seed_invalida(
    seed,
):
    with pytest.raises(
        ValueError,
        match="seed",
    ):
        PopulationGenerator(seed=seed)


def test_population_generator_aceita_seed_zero():
    generator = PopulationGenerator(seed=0)

    population = generator.generate(
        _build_population_generation_config(
            customer_count=2,
        )
    )

    assert len(population.profiles) == 2


def test_population_generator_isola_stream_de_login_de_config_transacional():
    config_com_heterogeneidade = _build_population_generation_config(
        customer_count=25,
        transaction_value_median_log_sigma=0.75,
        recent_login_failure_rate_mean=0.15,
    )
    config_sem_heterogeneidade = _build_population_generation_config(
        customer_count=25,
        transaction_value_median_log_sigma=0.0,
        recent_login_failure_rate_mean=0.15,
    )

    com_heterogeneidade = PopulationGenerator(
        seed=42,
    ).generate(config_com_heterogeneidade)

    sem_heterogeneidade = PopulationGenerator(
        seed=42,
    ).generate(config_sem_heterogeneidade)

    assert tuple(
        profile.recent_login_failure_rate for profile in com_heterogeneidade.profiles
    ) == tuple(
        profile.recent_login_failure_rate for profile in sem_heterogeneidade.profiles
    )


def test_population_generator_isola_stream_transacional_de_config_login():
    config_com_login = _build_population_generation_config(
        customer_count=25,
        transaction_value_median_log_sigma=0.75,
        recent_login_failure_rate_mean=0.15,
    )
    config_sem_login = _build_population_generation_config(
        customer_count=25,
        transaction_value_median_log_sigma=0.75,
        recent_login_failure_rate_mean=0.0,
    )

    com_login = PopulationGenerator(
        seed=42,
    ).generate(config_com_login)

    sem_login = PopulationGenerator(
        seed=42,
    ).generate(config_sem_login)

    assert tuple(
        profile.transaction_value_median for profile in com_login.profiles
    ) == tuple(profile.transaction_value_median for profile in sem_login.profiles)
