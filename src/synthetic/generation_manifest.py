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


@dataclass(frozen=True, slots=True)
class SeverityPolicyManifest:
    normal_min: float
    normal_max: float
    suspicious_min: float
    suspicious_max: float

    def __post_init__(self) -> None:
        campos = {
            "normal_min": self.normal_min,
            "normal_max": self.normal_max,
            "suspicious_min": self.suspicious_min,
            "suspicious_max": self.suspicious_max,
        }

        for nome, valor in campos.items():
            if (
                isinstance(valor, bool)
                or not isinstance(valor, (int, float))
                or not math.isfinite(valor)
                or not 0.0 <= valor <= 100.0
            ):
                raise ValueError(
                    f"{nome} deve ser numerico, finito e estar entre 0 e 100."
                )

        if self.normal_min > self.normal_max:
            raise ValueError("normal_min deve ser menor ou igual a normal_max.")

        if self.suspicious_min > self.suspicious_max:
            raise ValueError("suspicious_min deve ser menor ou igual a suspicious_max.")


@dataclass(frozen=True, slots=True)
class EventIntensityPolicyManifest:
    intensity_min: float
    intensity_max: float

    def __post_init__(self) -> None:
        campos = {
            "intensity_min": self.intensity_min,
            "intensity_max": self.intensity_max,
        }

        for nome, valor in campos.items():
            if (
                isinstance(valor, bool)
                or not isinstance(valor, (int, float))
                or not math.isfinite(valor)
                or not 0.0 <= valor <= 1.0
            ):
                raise ValueError(
                    f"{nome} deve ser numerico, finito e estar entre 0 e 1."
                )

        if self.intensity_min > self.intensity_max:
            raise ValueError("intensity_min deve ser menor ou igual a intensity_max.")


@dataclass(frozen=True, slots=True)
class ScenarioEffectManifest:
    transaction_value_median_multiplier: float
    transaction_value_sigma_multiplier: float
    recent_login_failure_rate_increment: float

    def __post_init__(self) -> None:
        valor = self.transaction_value_median_multiplier

        if (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not math.isfinite(valor)
            or valor <= 0
        ):
            raise ValueError(
                "transaction_value_median_multiplier deve ser "
                "numerico, finito e maior que zero."
            )

        valor = self.transaction_value_sigma_multiplier

        if (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not math.isfinite(valor)
            or valor < 0
        ):
            raise ValueError(
                "transaction_value_sigma_multiplier deve ser "
                "numerico, finito e maior ou igual a zero."
            )

        valor = self.recent_login_failure_rate_increment

        if (
            isinstance(valor, bool)
            or not isinstance(valor, (int, float))
            or not math.isfinite(valor)
            or valor < 0
        ):
            raise ValueError(
                "recent_login_failure_rate_increment deve ser "
                "numerico, finito e maior ou igual a zero."
            )


@dataclass(frozen=True, slots=True)
class ScenarioGenerationManifest:
    scenario: str
    scenario_effect: ScenarioEffectManifest | None = None
    intensity_policy: EventIntensityPolicyManifest | None = None

    def __post_init__(self) -> None:
        if (
            not isinstance(self.scenario, str)
            or not self.scenario.strip()
            or self.scenario != self.scenario.strip()
        ):
            raise ValueError(
                "scenario deve ser uma string nao vazia e sem whitespace externo."
            )

        if self.scenario_effect is not None and not isinstance(
            self.scenario_effect,
            ScenarioEffectManifest,
        ):
            raise ValueError("scenario_effect deve ser ScenarioEffectManifest ou None.")

        if self.intensity_policy is not None and not isinstance(
            self.intensity_policy,
            EventIntensityPolicyManifest,
        ):
            raise ValueError(
                "intensity_policy deve ser EventIntensityPolicyManifest ou None."
            )
