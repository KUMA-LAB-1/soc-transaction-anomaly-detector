from datetime import datetime

import numpy as np

from .contracts import GenerationTruth, SyntheticRecord
from .label_policy import OperationalLabelPolicy
from .population import CustomerBehaviorProfile, CustomerPopulation
from .scenario_effects import ScenarioEffect
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
        population: CustomerPopulation | None = None,
    ) -> None:
        if population is not None and not isinstance(
            population,
            CustomerPopulation,
        ):
            raise ValueError("population deve ser CustomerPopulation ou None.")

        self.seed = seed
        self._label_policy = label_policy
        self._population = population

        self._rng = np.random.default_rng(seed)

        customer_seed, login_seed = np.random.SeedSequence(seed).spawn(2)

        self._customer_rng = np.random.default_rng(customer_seed)
        self._login_rng = np.random.default_rng(login_seed)

        self._temporal = TemporalSampler(self._rng)
        self._proximo_id_transacao = 1

    def gerar_registros(
        self,
        cenario: ScenarioDefinition,
        *,
        quantidade: int,
        inicio: datetime,
        fim: datetime,
        scenario_effect: ScenarioEffect | None = None,
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
                scenario_effect=scenario_effect,
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
        scenario_effect: ScenarioEffect | None,
    ) -> SyntheticRecord:

        customer_profile = self._selecionar_customer_profile()

        valor_transacao = self._gerar_valor_transacao(
            cenario,
            customer_profile=customer_profile,
            scenario_effect=scenario_effect,
        )

        dispositivo_novo = self._sortear(cenario.probabilidade_dispositivo_novo)
        alteracao_limite = self._sortear(cenario.probabilidade_alteracao_limite)
        mudanca_localizacao = self._sortear(cenario.probabilidade_mudanca_localizacao)

        falhas_login = self._gerar_falhas_login(
            cenario,
            customer_profile=customer_profile,
        )

        tipo_transacao = str(
            self._rng.choice(
                TIPOS_TRANSACAO,
            )
        )

        cliente_pseudonimo = self._selecionar_cliente_pseudonimo(
            customer_profile,
        )

        status_transacao = self._label_policy.gerar_status(
            is_suspicious=cenario.is_suspicious,
            sorteio=float(self._rng.random()),
        )

        return SyntheticRecord(
            observables={
                "id_transacao": id_transacao,
                "cliente_pseudonimo": cliente_pseudonimo,
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

    def _selecionar_customer_profile(
        self,
    ) -> CustomerBehaviorProfile | None:
        if self._population is None:
            return None

        profile_index = int(
            self._customer_rng.integers(
                0,
                len(self._population.profiles),
            )
        )

        return self._population.profiles[profile_index]

    def _selecionar_cliente_pseudonimo(
        self,
        customer_profile: CustomerBehaviorProfile | None,
    ) -> str:
        if customer_profile is not None:
            return customer_profile.customer_pseudonym

        cliente = int(
            self._rng.integers(
                1,
                101,
            )
        )

        return f"cliente-{cliente:03d}"

    def _gerar_valor_transacao(
        self,
        cenario: ScenarioDefinition,
        *,
        customer_profile: CustomerBehaviorProfile | None,
        scenario_effect: ScenarioEffect | None,
    ) -> float:
        if customer_profile is None:
            valor_mediano = cenario.valor_mediano
            valor_sigma = cenario.valor_sigma
        else:
            valor_mediano = customer_profile.transaction_value_median
            valor_sigma = customer_profile.transaction_value_sigma

        if scenario_effect is not None:
            valor_mediano *= scenario_effect.transaction_value_median_multiplier
            valor_sigma *= scenario_effect.transaction_value_sigma_multiplier

        valor = self._rng.lognormal(
            mean=np.log(valor_mediano),
            sigma=valor_sigma,
        )

        return max(
            round(float(valor), 2),
            0.01,
        )

    def _sortear(self, probabilidade: float) -> bool:
        return bool(self._rng.random() < probabilidade)

    def _gerar_falhas_login(
        self,
        cenario: ScenarioDefinition,
        *,
        customer_profile: CustomerBehaviorProfile | None,
    ) -> int:
        if customer_profile is None:
            return int(
                self._rng.poisson(
                    cenario.media_falhas_login,
                )
            )

        return int(
            self._login_rng.poisson(
                customer_profile.recent_login_failure_rate,
            )
        )
