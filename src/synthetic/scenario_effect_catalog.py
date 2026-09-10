from types import MappingProxyType

from .scenario_effects import ScenarioEffect

_CENARIO_EFFECTS = {
    "baseline": ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    ),
    "credential_attack": ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=1.25,
    ),
    "account_takeover": ScenarioEffect(
        transaction_value_median_multiplier=1.5,
        transaction_value_sigma_multiplier=1.10,
        recent_login_failure_rate_increment=0.35,
    ),
    "location_anomaly": ScenarioEffect(
        transaction_value_median_multiplier=1.0,
        transaction_value_sigma_multiplier=1.0,
        recent_login_failure_rate_increment=0.0,
    ),
    "transaction_anomaly": ScenarioEffect(
        transaction_value_median_multiplier=2.0,
        transaction_value_sigma_multiplier=1.15,
        recent_login_failure_rate_increment=0.0,
    ),
}


CENARIO_EFFECTS_PADRAO = MappingProxyType(
    _CENARIO_EFFECTS,
)


def obter_efeito_cenario(
    nome: str,
) -> ScenarioEffect:
    """Retorna o efeito relativo associado a um cenário sintético conhecido."""
    try:
        return CENARIO_EFFECTS_PADRAO[nome]
    except KeyError as exc:
        raise ValueError(f"Cenário sintético desconhecido: {nome}.") from exc
