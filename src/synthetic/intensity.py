import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class EventIntensityPolicy:
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

    def gerar_intensidade(
        self,
        *,
        sorteio: float,
    ) -> float:
        if (
            isinstance(sorteio, bool)
            or not isinstance(sorteio, (int, float))
            or not math.isfinite(sorteio)
            or not 0.0 <= sorteio <= 1.0
        ):
            raise ValueError("sorteio deve ser numerico, finito e estar entre 0 e 1.")

        return self.intensity_min + (self.intensity_max - self.intensity_min) * sorteio
