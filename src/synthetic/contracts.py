from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class GenerationTruth:
    """Representa informações conhecidas somente pelo laboratório sintético."""

    scenario: str
    is_suspicious: bool
    attack_profile: str | None = None
    expected_mitre_techniques: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class SyntheticRecord:
    """Separa observáveis, labels operacionais e verdade de geração."""

    observables: dict[str, Any]
    operational_labels: dict[str, Any]
    truth: GenerationTruth
