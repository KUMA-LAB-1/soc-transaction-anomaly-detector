import math
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GenerationTruth:
    """Representa informações conhecidas somente pelo laboratório sintético."""

    scenario: str
    is_suspicious: bool
    attack_profile: str | None = None
    expected_mitre_techniques: tuple[str, ...] = ()
    severity_score: float | None = None
    event_intensity: float | None = None

    def __post_init__(self) -> None:
        if self.severity_score is not None:
            if (
                isinstance(self.severity_score, bool)
                or not isinstance(self.severity_score, (int, float))
                or not math.isfinite(self.severity_score)
                or not 0.0 <= self.severity_score <= 100.0
            ):
                raise ValueError(
                    "severity_score deve ser num\u00e9rico, finito e estar entre 0 e 100."
                )

        if self.event_intensity is not None:
            if (
                isinstance(self.event_intensity, bool)
                or not isinstance(self.event_intensity, (int, float))
                or not math.isfinite(self.event_intensity)
                or not 0.0 <= self.event_intensity <= 1.0
            ):
                raise ValueError(
                    "event_intensity deve ser numerico, finito e estar entre 0 e 1."
                )


@dataclass(frozen=True, slots=True)
class SyntheticRecord:
    """Separa observáveis, labels operacionais e verdade de geração."""

    observables: dict[str, Any]
    operational_labels: dict[str, Any]
    truth: GenerationTruth
