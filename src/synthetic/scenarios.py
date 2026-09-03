from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ScenarioDefinition:
    """Define parâmetros probabilísticos de um cenário sintético.

    Os valores representam configurações experimentais do laboratório e não
    estimativas empíricas de risco, fraude ou comportamento bancário real.
    """

    name: str
    is_suspicious: bool
    valor_mediano: float
    valor_sigma: float
    media_falhas_login: float
    probabilidade_madrugada: float
    probabilidade_dispositivo_novo: float
    probabilidade_alteracao_limite: float
    probabilidade_mudanca_localizacao: float
    expected_mitre_techniques: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        probabilidades = {
            "probabilidade_madrugada": self.probabilidade_madrugada,
            "probabilidade_dispositivo_novo": (self.probabilidade_dispositivo_novo),
            "probabilidade_alteracao_limite": (self.probabilidade_alteracao_limite),
            "probabilidade_mudanca_localizacao": (
                self.probabilidade_mudanca_localizacao
            ),
        }

        for nome, valor in probabilidades.items():
            if not 0.0 <= valor <= 1.0:
                raise ValueError(f"{nome} deve ser uma probabilidade entre 0 e 1.")

        if self.valor_mediano <= 0:
            raise ValueError("valor_mediano deve ser maior que zero.")

        if self.valor_sigma <= 0:
            raise ValueError("valor_sigma deve ser maior que zero.")

        if self.media_falhas_login < 0:
            raise ValueError("media_falhas_login deve ser maior ou igual a zero.")


CENARIOS_PADRAO = {
    "baseline": ScenarioDefinition(
        name="baseline",
        is_suspicious=False,
        valor_mediano=180.0,
        valor_sigma=0.65,
        media_falhas_login=0.15,
        probabilidade_madrugada=0.08,
        probabilidade_dispositivo_novo=0.08,
        probabilidade_alteracao_limite=0.04,
        probabilidade_mudanca_localizacao=0.07,
    ),
    "credential_attack": ScenarioDefinition(
        name="credential_attack",
        is_suspicious=True,
        valor_mediano=420.0,
        valor_sigma=1.05,
        media_falhas_login=2.6,
        probabilidade_madrugada=0.35,
        probabilidade_dispositivo_novo=0.28,
        probabilidade_alteracao_limite=0.18,
        probabilidade_mudanca_localizacao=0.30,
        expected_mitre_techniques=("T1110",),
    ),
    "account_takeover": ScenarioDefinition(
        name="account_takeover",
        is_suspicious=True,
        valor_mediano=1200.0,
        valor_sigma=1.10,
        media_falhas_login=0.8,
        probabilidade_madrugada=0.28,
        probabilidade_dispositivo_novo=0.72,
        probabilidade_alteracao_limite=0.58,
        probabilidade_mudanca_localizacao=0.46,
        expected_mitre_techniques=("T1098",),
    ),
    "location_anomaly": ScenarioDefinition(
        name="location_anomaly",
        is_suspicious=True,
        valor_mediano=350.0,
        valor_sigma=0.90,
        media_falhas_login=0.35,
        probabilidade_madrugada=0.22,
        probabilidade_dispositivo_novo=0.33,
        probabilidade_alteracao_limite=0.12,
        probabilidade_mudanca_localizacao=0.78,
        expected_mitre_techniques=("T1078",),
    ),
    "transaction_anomaly": ScenarioDefinition(
        name="transaction_anomaly",
        is_suspicious=True,
        valor_mediano=3500.0,
        valor_sigma=1.30,
        media_falhas_login=0.25,
        probabilidade_madrugada=0.25,
        probabilidade_dispositivo_novo=0.20,
        probabilidade_alteracao_limite=0.18,
        probabilidade_mudanca_localizacao=0.22,
    ),
}


def obter_cenario(nome: str) -> ScenarioDefinition:
    """Retorna um cenário sintético conhecido pelo laboratório."""
    try:
        return CENARIOS_PADRAO[nome]
    except KeyError as exc:
        raise ValueError(f"Cenário sintético desconhecido: {nome}.") from exc
