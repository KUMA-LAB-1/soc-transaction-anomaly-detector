from datetime import datetime

import numpy as np

from .contracts import GenerationTruth, SyntheticRecord
from .label_policy import OperationalLabelPolicy
from .scenarios import ScenarioDefinition
from .temporal import TemporalSampler

TIPOS_TRANSACAO = (
    "Pix",
    "TED",
    "DOC",
    "Cartão Virtual",
)


class StatisticalGenerator:
    """Gera registros sintéticos a partir de cenários probabilísticos.

    O gerador produz dados experimentais reproduzíveis por seed e permanece
    independente de banco de dados, persistência e do pipeline operacional.
    """

    def __init__(
        self,
        seed: int,
        label_policy: OperationalLabelPolicy,
    ) -> None:
        self.seed = seed
        self._label_policy = label_policy
        self._rng = np.random.default_rng(seed)
        self._temporal = TemporalSampler(self._rng)
        self._proximo_id_transacao = 1

    def gerar_registros(
        self,
        cenario: ScenarioDefinition,
        *,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
    ) -> list[SyntheticRecord]:
        """Gera registros sintéticos cronológicos para um cenário."""
        if not isinstance(quantidade, int) or isinstance(quantidade, bool):
            raise ValueError("quantidade deve ser um número inteiro positivo.")

        if quantidade <= 0:
            raise ValueError("quantidade deve ser maior que zero.")

        timestamps = self._temporal.gerar_timestamps(
            cenario,
            quantidade=quantidade,
            inicio=inicio,
            fim=fim,
        )

        id_inicial = self._proximo_id_transacao

        registros = [
            self._gerar_registro(
                cenario,
                id_transacao=id_inicial + indice,
                timestamp=timestamps[indice],
            )
            for indice in range(quantidade)
        ]

        self._proximo_id_transacao += quantidade

        return registros

    def _gerar_registro(
        self,
        cenario: ScenarioDefinition,
        *,
        id_transacao: int,
        timestamp: datetime,
    ) -> SyntheticRecord:

        valor_transacao = self._gerar_valor_transacao(cenario)

        dispositivo_novo = self._sortear(cenario.probabilidade_dispositivo_novo)
        alteracao_limite = self._sortear(cenario.probabilidade_alteracao_limite)
        mudanca_localizacao = self._sortear(cenario.probabilidade_mudanca_localizacao)

        falhas_login = int(
            self._rng.poisson(
                cenario.media_falhas_login,
            )
        )

        tipo_transacao = str(
            self._rng.choice(
                TIPOS_TRANSACAO,
            )
        )

        cliente = int(
            self._rng.integers(
                1,
                101,
            )
        )

        status_transacao = self._label_policy.gerar_status(
            is_suspicious=cenario.is_suspicious,
            sorteio=float(self._rng.random()),
        )

        return SyntheticRecord(
            observables={
                "id_transacao": id_transacao,
                "cliente_pseudonimo": f"cliente-{cliente:03d}",
                "data_hora_transacao": timestamp,
                "tipo_transacao": tipo_transacao,
                "valor_transacao": valor_transacao,
                "falhas_login_recentes": falhas_login,
                "dispositivo_novo_flag": dispositivo_novo,
                "alteracao_limite_flag": alteracao_limite,
                "mudanca_localizacao_flag": mudanca_localizacao,
            },
            operational_labels={
                "status_transacao": status_transacao,
            },
            truth=GenerationTruth(
                scenario=cenario.name,
                is_suspicious=cenario.is_suspicious,
                attack_profile=(cenario.name if cenario.is_suspicious else None),
                expected_mitre_techniques=(cenario.expected_mitre_techniques),
            ),
        )

    def _gerar_valor_transacao(
        self,
        cenario: ScenarioDefinition,
    ) -> float:
        valor = self._rng.lognormal(
            mean=np.log(cenario.valor_mediano),
            sigma=cenario.valor_sigma,
        )

        return max(
            round(float(valor), 2),
            0.01,
        )

    def _sortear(self, probabilidade: float) -> bool:
        return bool(self._rng.random() < probabilidade)
