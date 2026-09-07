import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScenarioEffect:
    """Define efeitos relativos de um cenário sobre um baseline sintético."""

    transaction_value_median_multiplier: float
    transaction_value_sigma_multiplier: float
    recent_login_failure_rate_increment: float

    def __post_init__(self) -> None:
        self._validate_positive_finite_number(
            "transaction_value_median_multiplier",
            self.transaction_value_median_multiplier,
        )
        self._validate_non_negative_finite_number(
            "transaction_value_sigma_multiplier",
            self.transaction_value_sigma_multiplier,
        )
        self._validate_non_negative_finite_number(
            "recent_login_failure_rate_increment",
            self.recent_login_failure_rate_increment,
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
