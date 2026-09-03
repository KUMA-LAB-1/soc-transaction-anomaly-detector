import math
from dataclasses import dataclass
from datetime import datetime

from .allocation import allocate_scenario_quantities
from .contracts import SyntheticRecord
from .scenarios import ScenarioDefinition
from .statistical import StatisticalGenerator


@dataclass(frozen=True, slots=True)
class ScenarioMix:
    cenario: ScenarioDefinition
    proporcao: float

    def __post_init__(self) -> None:
        if isinstance(self.proporcao, bool) or not isinstance(
            self.proporcao,
            (int, float),
        ):
            raise ValueError("proporcao deve ser numérica.")

        if not math.isfinite(self.proporcao):
            raise ValueError("proporcao deve ser finita.")

        if self.proporcao <= 0.0 or self.proporcao > 1.0:
            raise ValueError("proporcao deve estar no intervalo (0, 1].")


class MixedDatasetComposer:
    """Compõe datasets sintéticos a partir de múltiplos cenários."""

    def __init__(self, gerador: StatisticalGenerator) -> None:
        self._gerador = gerador

    def compor(
        self,
        misturas: list[ScenarioMix],
        *,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
    ) -> list[SyntheticRecord]:
        if isinstance(quantidade, bool) or not isinstance(
            quantidade,
            int,
        ):
            raise ValueError("quantidade deve ser um inteiro positivo.")

        if quantidade <= 0:
            raise ValueError("quantidade deve ser um inteiro positivo.")

        if not misturas:
            raise ValueError("mistura deve conter pelo menos um cenário.")

        soma_proporcoes = sum(mistura.proporcao for mistura in misturas)

        if not math.isclose(
            soma_proporcoes,
            1.0,
            rel_tol=0.0,
            abs_tol=1e-12,
        ):
            raise ValueError("as proporções devem somar 1.")

        quantidades = allocate_scenario_quantities(
            [mistura.proporcao for mistura in misturas],
            quantidade=quantidade,
        )

        registros: list[SyntheticRecord] = []

        for mistura, quantidade_cenario in zip(
            misturas,
            quantidades,
            strict=True,
        ):
            if quantidade_cenario == 0:
                continue

            registros.extend(
                self._gerador.gerar_registros(
                    mistura.cenario,
                    quantidade=quantidade_cenario,
                    inicio=inicio,
                    fim=fim,
                )
            )

        registros.sort(
            key=lambda registro: (
                registro.observables["data_hora_transacao"],
                registro.observables["id_transacao"],
            )
        )

        return registros
