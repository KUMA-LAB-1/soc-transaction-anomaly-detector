import math
from dataclasses import dataclass

from .behavior_flags import BehaviorFlagBaseline


@dataclass(frozen=True, slots=True)
class CustomerBehaviorProfile:
    """Representa o comportamento baseline de uma entidade sintética."""

    customer_pseudonym: str
    transaction_value_median: float
    transaction_value_sigma: float
    recent_login_failure_rate: float
    behavior_flag_baseline: BehaviorFlagBaseline | None = None

    def __post_init__(self) -> None:
        if self.behavior_flag_baseline is not None and not isinstance(
            self.behavior_flag_baseline,
            BehaviorFlagBaseline,
        ):
            raise ValueError(
                "behavior_flag_baseline deve ser BehaviorFlagBaseline ou None."
            )

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


@dataclass(frozen=True, slots=True)
class CustomerPopulation:
    """Representa uma população estável de perfis comportamentais sintéticos."""

    profiles: tuple[CustomerBehaviorProfile, ...]

    def __post_init__(self) -> None:
        if not isinstance(self.profiles, tuple):
            raise ValueError("profiles deve ser uma tuple.")

        if not self.profiles:
            raise ValueError("profiles não pode ser vazio.")

        if not all(
            isinstance(profile, CustomerBehaviorProfile) for profile in self.profiles
        ):
            raise ValueError("profiles deve conter apenas CustomerBehaviorProfile.")

        pseudonyms = tuple(profile.customer_pseudonym for profile in self.profiles)

        if len(set(pseudonyms)) != len(pseudonyms):
            raise ValueError("customer_pseudonym deve ser único na população.")

    def get_profile(
        self,
        customer_pseudonym: str,
    ) -> CustomerBehaviorProfile:
        for profile in self.profiles:
            if profile.customer_pseudonym == customer_pseudonym:
                return profile

        raise ValueError(f"customer_pseudonym desconhecido: {customer_pseudonym}.")
