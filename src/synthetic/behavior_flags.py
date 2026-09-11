import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class BehaviorFlagBaseline:
    """Define probabilidades baseline para observaveis booleanos sinteticos."""

    new_device_probability: float
    limit_change_probability: float
    location_change_probability: float

    def __post_init__(self) -> None:
        probabilities = {
            "new_device_probability": self.new_device_probability,
            "limit_change_probability": self.limit_change_probability,
            "location_change_probability": self.location_change_probability,
        }

        for name, value in probabilities.items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or not 0.0 <= value <= 1.0
            ):
                raise ValueError(
                    f"{name} deve ser numerico, finito e estar entre 0 e 1."
                )
