from collections.abc import Sequence


def allocate_scenario_quantities(
    proporcoes: Sequence[float],
    *,
    quantidade: int,
) -> tuple[int, ...]:
    quotas = [quantidade * proporcao for proporcao in proporcoes]
    quantidades = [int(quota) for quota in quotas]

    quantidade_restante = quantidade - sum(quantidades)

    indices_por_maior_resto = sorted(
        range(len(proporcoes)),
        key=lambda indice: quotas[indice] - quantidades[indice],
        reverse=True,
    )

    for indice in indices_por_maior_resto[:quantidade_restante]:
        quantidades[indice] += 1

    return tuple(quantidades)
