import math
from dataclasses import dataclass

STATUS_NORMAL = "Concluída"
STATUS_SUSPEITO = "Em Análise"


@dataclass(frozen=True, slots=True)
class OperationalLabelPolicy:
    """Configura divergências experimentais entre truth e rótulo operacional."""

    probabilidade_falso_positivo: float
    probabilidade_falso_negativo: float

    def __post_init__(self) -> None:
        probabilidades = (
            self.probabilidade_falso_positivo,
            self.probabilidade_falso_negativo,
        )

        for probabilidade in probabilidades:
            if isinstance(probabilidade, bool) or not isinstance(
                probabilidade,
                (int, float),
            ):
                raise ValueError("probabilidade deve ser numérica.")

            if not math.isfinite(probabilidade):
                raise ValueError("probabilidade deve ser finita.")

            if probabilidade < 0.0 or probabilidade > 1.0:
                raise ValueError("probabilidade deve estar entre 0 e 1.")

    def gerar_status(
        self,
        *,
        is_suspicious: bool,
        sorteio: float,
    ) -> str:
        if not isinstance(is_suspicious, bool):
            raise ValueError("is_suspicious deve ser bool.")

        if isinstance(sorteio, bool) or not isinstance(
            sorteio,
            (int, float),
        ):
            raise ValueError("sorteio deve ser numérico.")

        if not math.isfinite(sorteio):
            raise ValueError("sorteio deve ser finito.")

        if sorteio < 0.0 or sorteio >= 1.0:
            raise ValueError("sorteio deve estar no intervalo [0, 1).")

        if is_suspicious:
            if sorteio < self.probabilidade_falso_negativo:
                return STATUS_NORMAL

            return STATUS_SUSPEITO

        if sorteio < self.probabilidade_falso_positivo:
            return STATUS_SUSPEITO

        return STATUS_NORMAL
