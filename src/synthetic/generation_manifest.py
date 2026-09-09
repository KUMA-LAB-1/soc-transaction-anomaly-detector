import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeedStrategyManifest:
    strategy_version: str
    statistical_seed: int
    population_seed: int

    def __post_init__(self) -> None:
        if (
            not isinstance(self.strategy_version, str)
            or not self.strategy_version.strip()
        ):
            raise ValueError("strategy_version deve ser uma string nao vazia.")

        if (
            isinstance(self.statistical_seed, bool)
            or not isinstance(self.statistical_seed, int)
            or self.statistical_seed < 0
        ):
            raise ValueError("statistical_seed deve ser um inteiro nao negativo.")

        if (
            isinstance(self.population_seed, bool)
            or not isinstance(self.population_seed, int)
            or self.population_seed < 0
        ):
            raise ValueError("population_seed deve ser um inteiro nao negativo.")


@dataclass(frozen=True, slots=True)
class PopulationGenerationManifest:
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

        if (
            isinstance(self.transaction_value_median_base, bool)
            or not isinstance(self.transaction_value_median_base, (int, float))
            or not math.isfinite(self.transaction_value_median_base)
            or self.transaction_value_median_base <= 0
        ):
            raise ValueError(
                "transaction_value_median_base deve ser numerico, "
                "finito e maior que zero."
            )

        if (
            isinstance(self.transaction_value_median_log_sigma, bool)
            or not isinstance(
                self.transaction_value_median_log_sigma,
                (int, float),
            )
            or not math.isfinite(self.transaction_value_median_log_sigma)
            or self.transaction_value_median_log_sigma < 0
        ):
            raise ValueError(
                "transaction_value_median_log_sigma deve ser numerico, "
                "finito e nao negativo."
            )

        if (
            isinstance(self.transaction_value_sigma, bool)
            or not isinstance(self.transaction_value_sigma, (int, float))
            or not math.isfinite(self.transaction_value_sigma)
            or self.transaction_value_sigma <= 0
        ):
            raise ValueError(
                "transaction_value_sigma deve ser numerico, finito e maior que zero."
            )

        if (
            isinstance(self.recent_login_failure_rate_mean, bool)
            or not isinstance(
                self.recent_login_failure_rate_mean,
                (int, float),
            )
            or not math.isfinite(self.recent_login_failure_rate_mean)
            or self.recent_login_failure_rate_mean < 0
        ):
            raise ValueError(
                "recent_login_failure_rate_mean deve ser numerico, "
                "finito e maior ou igual a zero."
            )

        if (
            isinstance(self.recent_login_failure_rate_shape, bool)
            or not isinstance(
                self.recent_login_failure_rate_shape,
                (int, float),
            )
            or not math.isfinite(self.recent_login_failure_rate_shape)
            or self.recent_login_failure_rate_shape <= 0
        ):
            raise ValueError(
                "recent_login_failure_rate_shape deve ser numerico, "
                "finito e maior que zero."
            )
