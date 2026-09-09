from dataclasses import dataclass

from .intensity import EventIntensityPolicy
from .population_generation import PopulationGenerationConfig
from .scenario_effects import ScenarioEffect
from .severity import SeverityPolicy


@dataclass(frozen=True, slots=True)
class ScenarioGenerationConfig:
    scenario: str
    scenario_effect: ScenarioEffect | None = None
    intensity_policy: EventIntensityPolicy | None = None

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
            ScenarioEffect,
        ):
            raise ValueError("scenario_effect deve ser ScenarioEffect ou None.")

        if self.intensity_policy is not None and not isinstance(
            self.intensity_policy,
            EventIntensityPolicy,
        ):
            raise ValueError("intensity_policy deve ser EventIntensityPolicy ou None.")


@dataclass(frozen=True, slots=True)
class SyntheticGenerationConfig:
    population_config: PopulationGenerationConfig | None = None
    severity_policy: SeverityPolicy | None = None
    scenario_configs: tuple[ScenarioGenerationConfig, ...] = ()

    def __post_init__(self) -> None:
        if self.population_config is not None and not isinstance(
            self.population_config,
            PopulationGenerationConfig,
        ):
            raise ValueError(
                "population_config deve ser PopulationGenerationConfig ou None."
            )

        if self.severity_policy is not None and not isinstance(
            self.severity_policy,
            SeverityPolicy,
        ):
            raise ValueError("severity_policy deve ser SeverityPolicy ou None.")

        if not isinstance(self.scenario_configs, tuple):
            raise ValueError("scenario_configs deve ser uma tuple.")

        if not all(
            isinstance(config, ScenarioGenerationConfig)
            for config in self.scenario_configs
        ):
            raise ValueError(
                "scenario_configs deve conter apenas ScenarioGenerationConfig."
            )

        scenario_names = tuple(config.scenario for config in self.scenario_configs)

        if len(scenario_names) != len(set(scenario_names)):
            raise ValueError("scenario_configs nao pode conter cenarios duplicados.")
