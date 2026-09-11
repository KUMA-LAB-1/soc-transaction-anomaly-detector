import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScenarioEffect:
    """Define efeitos relativos de um cenário sobre um baseline sintético."""

    transaction_value_median_multiplier: float
    transaction_value_sigma_multiplier: float
    recent_login_failure_rate_increment: float
    new_device_probability_delta: float = 0.0
    limit_change_probability_delta: float = 0.0
    location_change_probability_delta: float = 0.0

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

        self._validate_probability_delta(
            "new_device_probability_delta",
            self.new_device_probability_delta,
        )
        self._validate_probability_delta(
            "limit_change_probability_delta",
            self.limit_change_probability_delta,
        )
        self._validate_probability_delta(
            "location_change_probability_delta",
            self.location_change_probability_delta,
        )

    @property
    def is_neutral(self) -> bool:
        return (
            self.transaction_value_median_multiplier == 1.0
            and self.transaction_value_sigma_multiplier == 1.0
            and self.recent_login_failure_rate_increment == 0.0
            and self.new_device_probability_delta == 0.0
            and self.limit_change_probability_delta == 0.0
            and self.location_change_probability_delta == 0.0
        )

    def aplicar_intensidade(
        self,
        intensidade: float,
    ) -> "ScenarioEffect":
        if (
            isinstance(intensidade, bool)
            or not isinstance(intensidade, (int, float))
            or not math.isfinite(intensidade)
            or not 0.0 <= intensidade <= 1.0
        ):
            raise ValueError(
                "intensidade deve ser numerica, finita e estar entre 0 e 1."
            )

        return ScenarioEffect(
            transaction_value_median_multiplier=(
                1.0 + (self.transaction_value_median_multiplier - 1.0) * intensidade
            ),
            transaction_value_sigma_multiplier=(
                1.0 + (self.transaction_value_sigma_multiplier - 1.0) * intensidade
            ),
            recent_login_failure_rate_increment=(
                self.recent_login_failure_rate_increment * intensidade
            ),
            new_device_probability_delta=(
                self.new_device_probability_delta * intensidade
            ),
            limit_change_probability_delta=(
                self.limit_change_probability_delta * intensidade
            ),
            location_change_probability_delta=(
                self.location_change_probability_delta * intensidade
            ),
        )

    @staticmethod
    def _validate_probability_delta(
        name: str,
        value: float,
    ) -> None:
        if (
            isinstance(value, bool)
            or not isinstance(value, (int, float))
            or not math.isfinite(value)
            or not -1.0 <= value <= 1.0
        ):
            raise ValueError(f"{name} deve ser numerico, finito e estar entre -1 e 1.")

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
