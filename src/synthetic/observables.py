from collections.abc import Mapping
from math import isfinite


def get_transaction_value(
    observables: Mapping[str, object],
) -> float:
    if "valor_transacao" not in observables:
        raise ValueError("observables deve conter valor_transacao.")

    value = observables["valor_transacao"]

    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError("valor_transacao deve ser numerico.")

    if not isfinite(value):
        raise ValueError("valor_transacao deve ser finito.")

    return float(value)


def get_recent_login_failures(
    observables: Mapping[str, object],
) -> int:
    if "falhas_login_recentes" not in observables:
        raise ValueError("observables deve conter falhas_login_recentes.")

    value = observables["falhas_login_recentes"]

    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("falhas_login_recentes deve ser inteiro.")

    if value < 0:
        raise ValueError("falhas_login_recentes deve ser maior ou igual a zero.")

    return value
