import pandas as pd

from ..data.columns import resolver_coluna_cliente


def criar_features(df: pd.DataFrame) -> pd.DataFrame:
    """Cria features históricas e sinais utilizados pelos modelos do SOC."""
    col_cliente = resolver_coluna_cliente(df)

    df["data_hora_transacao"] = pd.to_datetime(df["data_hora_transacao"])

    # Ordem cronológica global. O cliente é usado apenas como critério
    # determinístico de desempate quando duas transações possuem o mesmo horário.
    df = df.sort_values(
        ["data_hora_transacao", col_cliente],
        kind="stable",
    ).reset_index(drop=True)

    grupo_cliente = df.groupby(col_cliente)["valor_transacao"]

    # Histórico individual do cliente.
    # shift(1) garante que a transação atual nunca participe do próprio baseline.
    df["media_historica_cliente"] = grupo_cliente.transform(
        lambda serie: serie.shift(1).expanding().mean()
    )

    df["desvio_historico_cliente"] = grupo_cliente.transform(
        lambda serie: serie.shift(1).expanding().std()
    )

    df["qtd_transacoes_anteriores"] = df.groupby(col_cliente).cumcount()

    # Fallback global também estritamente causal.
    # Apenas transações cronologicamente anteriores podem participar dele.
    historico_global = df["valor_transacao"].shift(1)

    media_global_historica = historico_global.expanding().mean()
    desvio_global_historico = historico_global.expanding().std()

    df["media_historica_cliente"] = (
        df["media_historica_cliente"]
        .fillna(media_global_historica)
        .fillna(df["valor_transacao"])
    )

    df["desvio_historico_cliente"] = (
        df["desvio_historico_cliente"]
        .fillna(desvio_global_historico)
        .fillna(1.0)
        .replace(0, 0.01)
    )

    df["zscore_valor_cliente"] = (
        df["valor_transacao"] - df["media_historica_cliente"]
    ) / df["desvio_historico_cliente"]

    df["dia_semana"] = pd.to_datetime(df["data_hora_transacao"]).dt.dayofweek

    colunas_com_padrao = {
        "falhas_login_recentes": 0,
        "dispositivo_novo_flag": False,
        "alteracao_limite_flag": False,
        "mudanca_localizacao_flag": False,
    }

    for coluna, valor_padrao in colunas_com_padrao.items():
        if coluna not in df.columns:
            df[coluna] = valor_padrao

    df["falhas_login_recentes"] = df["falhas_login_recentes"].fillna(0).astype(int)

    colunas_booleanas = (
        "dispositivo_novo_flag",
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    )

    for coluna in colunas_booleanas:
        df[coluna] = df[coluna].fillna(False).astype(bool)

    return df
