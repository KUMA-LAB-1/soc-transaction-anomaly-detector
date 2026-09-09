from dataclasses import dataclass

from .intensity import EventIntensityPolicy
from .scenario_effects import ScenarioEffect


@dataclass(frozen=True, slots=True)
class ScenarioGenerationConfig:
    scenario: str
    scenario_effect: ScenarioEffect | None = None
    intensity_policy: EventIntensityPolicy | None = None

    def __post_init__(self) -> None:
        if not isinstance(self.scenario, str) or not self.scenario.strip():
            raise ValueError("scenario deve ser uma string nao vazia.")

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
