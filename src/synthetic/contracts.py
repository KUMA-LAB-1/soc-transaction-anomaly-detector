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

    def __post_init__(self) -> None:
        if self.severity_score is None:
            return

        if (
            isinstance(self.severity_score, bool)
            or not isinstance(self.severity_score, (int, float))
            or not math.isfinite(self.severity_score)
            or not 0.0 <= self.severity_score <= 100.0
        ):
            raise ValueError(
                "severity_score deve ser numérico, finito e estar entre 0 e 100."
            )


@dataclass(frozen=True, slots=True)
class SyntheticRecord:
    """Separa observáveis, labels operacionais e verdade de geração."""

    observables: dict[str, Any]
    operational_labels: dict[str, Any]
    truth: GenerationTruth
