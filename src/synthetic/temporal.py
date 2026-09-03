from bisect import bisect_right
from datetime import datetime, timedelta
from itertools import accumulate

import numpy as np

from .scenarios import ScenarioDefinition


class TemporalSampler:
    """Gera timestamps reproduzíveis para datasets sintéticos."""

    def __init__(self, rng: np.random.Generator) -> None:
        self._rng = rng

    def gerar_timestamps(
        self,
        cenario: ScenarioDefinition,
        *,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
    ) -> list[datetime]:
        if fim <= inicio:
            raise ValueError("fim deve ser posterior a inicio.")

        return self._gerar_timestamps_na_janela(
            cenario,
            quantidade=quantidade,
            inicio=inicio,
            fim=fim,
        )

    def _gerar_timestamps_na_janela(
        self,
        cenario: ScenarioDefinition,
        *,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
    ) -> list[datetime]:
        intervalos_madrugada = self._construir_intervalos_temporais(
            inicio,
            fim,
            madrugada=True,
        )
        intervalos_dia = self._construir_intervalos_temporais(
            inicio,
            fim,
            madrugada=False,
        )

        capacidade_madrugada = self._capacidade_intervalos(intervalos_madrugada)
        capacidade_dia = self._capacidade_intervalos(intervalos_dia)
        capacidade_total = capacidade_madrugada + capacidade_dia

        if quantidade > capacidade_total:
            raise ValueError(
                "janela temporal não possui resolução suficiente "
                "para a quantidade solicitada."
            )

        if capacidade_madrugada == 0:
            quantidade_madrugada = 0
        elif capacidade_dia == 0:
            quantidade_madrugada = quantidade
        else:
            quantidade_madrugada = int(
                self._rng.binomial(
                    quantidade,
                    cenario.probabilidade_madrugada,
                )
            )

        quantidade_madrugada = min(
            quantidade_madrugada,
            capacidade_madrugada,
        )

        quantidade_dia = quantidade - quantidade_madrugada

        if quantidade_dia > capacidade_dia:
            excesso = quantidade_dia - capacidade_dia
            quantidade_dia = capacidade_dia
            quantidade_madrugada += excesso

        offsets = [
            *self._sortear_offsets_unicos(
                intervalos_madrugada,
                quantidade_madrugada,
            ),
            *self._sortear_offsets_unicos(
                intervalos_dia,
                quantidade_dia,
            ),
        ]

        timestamps = [inicio + timedelta(microseconds=offset) for offset in offsets]

        return sorted(timestamps)

    def _construir_intervalos_temporais(
        self,
        inicio: datetime,
        fim: datetime,
        *,
        madrugada: bool,
    ) -> list[tuple[int, int]]:
        intervalos = []

        cursor = inicio.replace(
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        )

        while cursor < fim:
            if madrugada:
                periodo_inicio = cursor
                periodo_fim = cursor + timedelta(hours=6)
            else:
                periodo_inicio = cursor + timedelta(hours=6)
                periodo_fim = cursor + timedelta(days=1)

            recorte_inicio = max(inicio, periodo_inicio)
            recorte_fim = min(fim, periodo_fim)

            if recorte_inicio < recorte_fim:
                offset_inicio = self._timedelta_microsegundos(recorte_inicio - inicio)
                offset_fim = self._timedelta_microsegundos(recorte_fim - inicio)

                intervalos.append(
                    (
                        offset_inicio,
                        offset_fim,
                    )
                )

            cursor += timedelta(days=1)

        return intervalos

    @staticmethod
    def _capacidade_intervalos(
        intervalos: list[tuple[int, int]],
    ) -> int:
        return sum(fim - inicio for inicio, fim in intervalos)

    def _sortear_offsets_unicos(
        self,
        intervalos: list[tuple[int, int]],
        quantidade: int,
    ) -> list[int]:
        if quantidade == 0:
            return []

        tamanhos = [fim - inicio for inicio, fim in intervalos]
        capacidade_total = sum(tamanhos)

        if quantidade > capacidade_total:
            raise ValueError("intervalo temporal não possui posições suficientes.")

        limites = list(accumulate(tamanhos))

        posicoes_escolhidas: list[int] = []
        posicoes_vistas: set[int] = set()

        while len(posicoes_escolhidas) < quantidade:
            restante = quantidade - len(posicoes_escolhidas)

            candidatos = self._rng.integers(
                0,
                capacidade_total,
                size=max(restante * 2, 32),
            )

            for candidato in candidatos:
                posicao = int(candidato)

                if posicao in posicoes_vistas:
                    continue

                posicoes_vistas.add(posicao)
                posicoes_escolhidas.append(posicao)

                if len(posicoes_escolhidas) == quantidade:
                    break

        offsets = []

        for posicao in posicoes_escolhidas:
            indice_intervalo = bisect_right(
                limites,
                posicao,
            )

            limite_anterior = (
                0 if indice_intervalo == 0 else limites[indice_intervalo - 1]
            )

            inicio_intervalo = intervalos[indice_intervalo][0]

            offsets.append(inicio_intervalo + posicao - limite_anterior)

        return offsets

    @staticmethod
    def _timedelta_microsegundos(valor: timedelta) -> int:
        return (valor.days * 86_400 + valor.seconds) * 1_000_000 + valor.microseconds
