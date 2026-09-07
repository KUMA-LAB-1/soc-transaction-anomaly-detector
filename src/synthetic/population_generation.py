import math
from dataclasses import dataclass

import numpy as np

from .population import CustomerBehaviorProfile, CustomerPopulation


@dataclass(frozen=True, slots=True)
class PopulationGenerationConfig:
    """Configura a geração reproduzível de uma população sintética."""

    customer_count: int
    transaction_value_median_base: float
    transaction_value_median_log_sigma: float
    transaction_value_sigma: float
    recent_login_failure_rate_mean: float
    recent_login_failure_rate_shape: float

    def __post_init__(self) -> None:
        if (
            isinstance(self.customer_count, bool)
            or not isinstance(self.customer_count, int)
            or self.customer_count <= 0
        ):
            raise ValueError("customer_count deve ser um inteiro positivo.")

        self._validate_positive_finite_number(
            "transaction_value_median_base",
            self.transaction_value_median_base,
        )
        self._validate_non_negative_finite_number(
            "transaction_value_median_log_sigma",
            self.transaction_value_median_log_sigma,
        )
        self._validate_positive_finite_number(
            "transaction_value_sigma",
            self.transaction_value_sigma,
        )
        self._validate_non_negative_finite_number(
            "recent_login_failure_rate_mean",
            self.recent_login_failure_rate_mean,
        )
        self._validate_positive_finite_number(
            "recent_login_failure_rate_shape",
            self.recent_login_failure_rate_shape,
        )

    @staticmethod
    def _validate_positive_finite_number(
        name: str,
        value: float,
    ) -> None:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value <= 0
        ):
            raise ValueError(f"{name} deve ser numérico, finito e maior que zero.")

    @staticmethod
    def _validate_non_negative_finite_number(
        name: str,
        value: float,
    ) -> None:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or value < 0
        ):
            raise ValueError(
                f"{name} deve ser numérico, finito e maior ou igual a zero."
            )


class PopulationGenerator:
    """Gera populações sintéticas reproduzíveis a partir de uma configuração."""

    def __init__(
        self,
        seed: int,
    ) -> None:
        if isinstance(seed, bool) or not isinstance(seed, int) or seed < 0:
            raise ValueError("seed deve ser um inteiro não negativo.")

        self.seed = seed

    def generate(
        self,
        config: PopulationGenerationConfig,
    ) -> CustomerPopulation:
        seed_sequence = np.random.SeedSequence(self.seed)

        transaction_seed, login_seed = seed_sequence.spawn(2)

        transaction_rng = np.random.default_rng(transaction_seed)
        login_rng = np.random.default_rng(login_seed)

        profiles = tuple(
            self._generate_profile(
                transaction_rng,
                login_rng,
                config,
                customer_index=customer_index,
            )
            for customer_index in range(
                1,
                config.customer_count + 1,
            )
        )

        return CustomerPopulation(
            profiles=profiles,
        )

    @staticmethod
    def _generate_profile(
        transaction_rng: np.random.Generator,
        login_rng: np.random.Generator,
        config: PopulationGenerationConfig,
        *,
        customer_index: int,
    ) -> CustomerBehaviorProfile:
        transaction_value_median = (
            config.transaction_value_median_base
            if config.transaction_value_median_log_sigma == 0
            else float(
                transaction_rng.lognormal(
                    mean=np.log(config.transaction_value_median_base),
                    sigma=config.transaction_value_median_log_sigma,
                )
            )
        )

        recent_login_failure_rate = (
            0.0
            if config.recent_login_failure_rate_mean == 0
            else float(
                login_rng.gamma(
                    shape=config.recent_login_failure_rate_shape,
                    scale=(
                        config.recent_login_failure_rate_mean
                        / config.recent_login_failure_rate_shape
                    ),
                )
            )
        )

        return CustomerBehaviorProfile(
            customer_pseudonym=f"cliente-{customer_index:03d}",
            transaction_value_median=transaction_value_median,
            transaction_value_sigma=config.transaction_value_sigma,
            recent_login_failure_rate=recent_login_failure_rate,
        )
