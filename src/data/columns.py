import pandas as pd

COLUNA_CLIENTE_PADRAO = "cliente_pseudonimo"


def resolver_coluna_cliente(df: pd.DataFrame) -> str:
    """Retorna a coluna canônica de identidade pseudonimizada do cliente.

    O pipeline exige ``cliente_pseudonimo`` como parte do contrato do dataset
    SOC. A ausência dessa coluna indica incompatibilidade entre a origem dos
    dados e o contrato esperado pelo pipeline.
    """
    if COLUNA_CLIENTE_PADRAO not in df.columns:
        raise ValueError(
            "Dataset SOC inválido: coluna obrigatória "
            "'cliente_pseudonimo' ausente."
        )

    return COLUNA_CLIENTE_PADRAO
