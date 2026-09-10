import math
from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class SeverityPolicy:
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

    def gerar_score(
        self,
        *,
        is_suspicious: bool,
        sorteio: float,
    ) -> float:
        if not isinstance(is_suspicious, bool):
            raise ValueError("is_suspicious deve ser bool.")

        if (
            isinstance(sorteio, bool)
            or not isinstance(sorteio, (int, float))
            or not math.isfinite(sorteio)
            or not 0.0 <= sorteio <= 1.0
        ):
            raise ValueError("sorteio deve ser numerico, finito e estar entre 0 e 1.")

        if is_suspicious:
            minimo = self.suspicious_min
            maximo = self.suspicious_max
        else:
            minimo = self.normal_min
            maximo = self.normal_max

        return minimo + (maximo - minimo) * sorteio
