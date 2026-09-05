import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class CustomerBehaviorProfile:
    """Representa o comportamento baseline de uma entidade sintética."""

    customer_pseudonym: str
    transaction_value_median: float
    transaction_value_sigma: float
    recent_login_failure_rate: float

    def __post_init__(self) -> None:
        if (
            not isinstance(self.customer_pseudonym, str)
            or not self.customer_pseudonym.strip()
        ):
            raise ValueError("customer_pseudonym deve ser uma string não vazia.")

        self._validate_positive_finite_number(
            "transaction_value_median",
            self.transaction_value_median,
        )
        self._validate_positive_finite_number(
            "transaction_value_sigma",
            self.transaction_value_sigma,
        )
        self._validate_non_negative_finite_number(
            "recent_login_failure_rate",
            self.recent_login_failure_rate,
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
