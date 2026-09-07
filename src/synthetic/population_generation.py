import math
from dataclasses import dataclass


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
