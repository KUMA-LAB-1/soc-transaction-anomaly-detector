import pandas as pd

COLUNAS_CLIENTE_CANDIDATAS = (
    "cliente_pseudonimo",
    "cliente_anonimizado",
    "cliente_anonimado",
)

COLUNA_CLIENTE_PADRAO = "cliente_pseudonimo"
CLIENTE_ANONIMIZADO_PADRAO = "Usuário Anonimizado"


def resolver_coluna_cliente(df: pd.DataFrame) -> str:
    """Retorna a coluna usada para identificar clientes pseudonimizados.

    Caso nenhuma coluna conhecida esteja disponível, cria uma coluna
    pseudonimizada padrão para preservar o funcionamento do pipeline.
    """
    for coluna in COLUNAS_CLIENTE_CANDIDATAS:
        if coluna in df.columns:
            return coluna

    df[COLUNA_CLIENTE_PADRAO] = CLIENTE_ANONIMIZADO_PADRAO
    return COLUNA_CLIENTE_PADRAO
