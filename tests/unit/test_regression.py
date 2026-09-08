import numpy as np
import pandas as pd
import pytest
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import KFold, train_test_split

from src.models.regression import (
    FEATURES_REGRESSAO,
    MAPA_SEVERIDADE_STATUS,
    SEVERIDADE_PADRAO,
    treinar_regressao_severidade,
)


def criar_dataset_regressao() -> pd.DataFrame:
    registros = []

    status = [
        "Aprovada",
        "Concluída",
        "Em Análise",
        "Bloqueada por Suspeita",
    ]

    for i in range(40):
        status_transacao = status[i % len(status)]

        severidade_indicativa = {
            "Aprovada": 5,
            "Concluída": 5,
            "Em Análise": 55,
            "Bloqueada por Suspeita": 95,
        }[status_transacao]

        registros.append(
            {
                "data_hora_transacao": (
                    pd.Timestamp("2026-01-01") + pd.Timedelta(hours=i)
                ),
                "status_transacao": status_transacao,
                "valor_transacao": 100.0 + severidade_indicativa * 10 + i,
                "hora": i % 24,
                "media_historica_cliente": 100.0 + i,
                "desvio_historico_cliente": 10.0 + (i % 5),
                "zscore_valor_cliente": severidade_indicativa / 20,
                "qtd_transacoes_anteriores": i,
                "dia_semana": i % 7,
                "falhas_login_recentes": (
                    3 if status_transacao == "Bloqueada por Suspeita" else 0
                ),
            }
        )

    return pd.DataFrame(registros)


def criar_dataset_regressao_com_extrapolacao() -> pd.DataFrame:
    df = criar_dataset_regressao()

    severidade = (
        df["status_transacao"].map(MAPA_SEVERIDADE_STATUS).fillna(SEVERIDADE_PADRAO)
    )

    df["valor_transacao"] = 100.0
    df["hora"] = 12
    df["media_historica_cliente"] = 100.0
    df["desvio_historico_cliente"] = 10.0
    df["zscore_valor_cliente"] = severidade / 10
    df["qtd_transacoes_anteriores"] = 0
    df["dia_semana"] = 1
    df["falhas_login_recentes"] = 0

    indices = np.arange(len(df))
    _, indices_teste = train_test_split(
        indices,
        test_size=0.25,
        random_state=42,
    )

    df.loc[
        int(indices_teste[0]),
        "zscore_valor_cliente",
    ] = 1_000.0

    return df


def test_treinar_regressao_retorna_modelo():
    df = criar_dataset_regressao()

    resultado = treinar_regressao_severidade(df)

    assert isinstance(resultado["modelo"], LinearRegression)


def test_regressao_retorna_predicao_para_todos_os_registros():
    df = criar_dataset_regressao()

    resultado = treinar_regressao_severidade(df)

    assert len(resultado["score_risco_predito"]) == len(df)


def test_scores_preditos_ficam_entre_zero_e_cem():
    df = criar_dataset_regressao()

    resultado = treinar_regressao_severidade(df)

    scores = resultado["score_risco_predito"]

    assert np.all(scores >= 0)
    assert np.all(scores <= 100)


def test_regressao_retorna_metricas_esperadas():
    df = criar_dataset_regressao()

    resultado = treinar_regressao_severidade(df)

    metricas = resultado["metricas"]

    assert set(metricas) == {
        "estrategia_validacao",
        "n_treino",
        "n_teste",
        "r2_teste",
        "mae_teste",
        "rmse_teste",
        "r2_cv_media",
        "r2_cv_desvio",
    }

    assert metricas["estrategia_validacao"] == "random"
    assert metricas["n_treino"] == 30
    assert metricas["n_teste"] == 10
    assert isinstance(metricas["r2_teste"], float)
    assert isinstance(metricas["mae_teste"], float)
    assert isinstance(metricas["rmse_teste"], float)
    assert isinstance(metricas["r2_cv_media"], float)
    assert isinstance(metricas["r2_cv_desvio"], float)


def test_erros_da_regressao_nao_sao_negativos():
    df = criar_dataset_regressao()

    resultado = treinar_regressao_severidade(df)

    metricas = resultado["metricas"]

    assert metricas["mae_teste"] >= 0
    assert metricas["rmse_teste"] >= 0


def test_funcao_nao_altera_dataframe_original():
    df = criar_dataset_regressao()

    assert "severidade_real" not in df.columns

    treinar_regressao_severidade(df)

    assert "severidade_real" not in df.columns


def test_regressao_mantem_validacao_random_por_padrao():
    df = criar_dataset_regressao()

    resultado = treinar_regressao_severidade(df)

    assert resultado["metricas"]["estrategia_validacao"] == "random"


def test_regressao_suporta_validacao_temporal():
    df = criar_dataset_regressao()

    resultado = treinar_regressao_severidade(
        df,
        estrategia_validacao="temporal",
    )

    metricas = resultado["metricas"]

    assert metricas["estrategia_validacao"] == "temporal"
    assert metricas["n_treino"] == 30
    assert metricas["n_teste"] == 10


def test_regressao_temporal_produz_cv_temporal():
    df = criar_dataset_regressao()

    resultado = treinar_regressao_severidade(
        df,
        estrategia_validacao="temporal",
    )

    metricas = resultado["metricas"]

    assert isinstance(metricas["r2_cv_media"], float)
    assert isinstance(metricas["r2_cv_desvio"], float)


def test_regressao_rejeita_estrategia_desconhecida():
    df = criar_dataset_regressao()

    with pytest.raises(
        ValueError,
        match="estrategia_validacao",
    ):
        treinar_regressao_severidade(
            df,
            estrategia_validacao="necromancia",
        )


def test_metricas_holdout_usam_score_operacional_limitado():
    df = criar_dataset_regressao_com_extrapolacao()

    resultado = treinar_regressao_severidade(df)

    X = df[FEATURES_REGRESSAO].fillna(0)
    y = df["status_transacao"].map(MAPA_SEVERIDADE_STATUS).fillna(SEVERIDADE_PADRAO)

    indices = np.arange(len(df))
    _, indices_teste = train_test_split(
        indices,
        test_size=0.25,
        random_state=42,
    )

    predicao_raw = resultado["modelo"].predict(X.iloc[indices_teste])
    predicao_operacional = np.clip(
        predicao_raw,
        0,
        100,
    )

    assert np.any((predicao_raw < 0) | (predicao_raw > 100))

    metricas = resultado["metricas"]

    assert metricas["r2_teste"] == pytest.approx(
        r2_score(
            y.iloc[indices_teste],
            predicao_operacional,
        )
    )
    assert metricas["mae_teste"] == pytest.approx(
        mean_absolute_error(
            y.iloc[indices_teste],
            predicao_operacional,
        )
    )
    assert metricas["rmse_teste"] == pytest.approx(
        np.sqrt(
            mean_squared_error(
                y.iloc[indices_teste],
                predicao_operacional,
            )
        )
    )


def test_r2_cv_usa_score_operacional_limitado():
    df = criar_dataset_regressao_com_extrapolacao()

    resultado = treinar_regressao_severidade(df)

    X = df[FEATURES_REGRESSAO].fillna(0)
    y = df["status_transacao"].map(MAPA_SEVERIDADE_STATUS).fillna(SEVERIDADE_PADRAO)

    scores_operacionais = []
    houve_extrapolacao = False

    for indices_treino, indices_teste in KFold(
        n_splits=5,
        shuffle=False,
    ).split(X):
        modelo = LinearRegression()
        modelo.fit(
            X.iloc[indices_treino],
            y.iloc[indices_treino],
        )

        predicao_raw = modelo.predict(X.iloc[indices_teste])

        houve_extrapolacao = (
            houve_extrapolacao or np.any(predicao_raw < 0) or np.any(predicao_raw > 100)
        )

        predicao_operacional = np.clip(
            predicao_raw,
            0,
            100,
        )

        scores_operacionais.append(
            r2_score(
                y.iloc[indices_teste],
                predicao_operacional,
            )
        )

    assert houve_extrapolacao

    metricas = resultado["metricas"]

    assert metricas["r2_cv_media"] == pytest.approx(np.mean(scores_operacionais))
    assert metricas["r2_cv_desvio"] == pytest.approx(np.std(scores_operacionais))
