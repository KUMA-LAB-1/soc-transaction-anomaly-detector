import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, train_test_split

from .validation import criar_folds_temporais, dividir_holdout_temporal

MAPA_SEVERIDADE_STATUS = {
    "Aprovada": 5,
    "Concluída": 5,
    "Em Análise": 55,
    "Bloqueada por Suspeita": 95,
}

SEVERIDADE_PADRAO = 30

FEATURES_REGRESSAO = [
    "valor_transacao",
    "hora",
    "media_historica_cliente",
    "desvio_historico_cliente",
    "zscore_valor_cliente",
    "qtd_transacoes_anteriores",
    "dia_semana",
    "falhas_login_recentes",
]

ESTRATEGIA_RANDOM = "random"
ESTRATEGIA_TEMPORAL = "temporal"

ESTRATEGIAS_VALIDACAO = {
    ESTRATEGIA_RANDOM,
    ESTRATEGIA_TEMPORAL,
}


def treinar_regressao_severidade(
    df: pd.DataFrame,
    *,
    estrategia_validacao: str = ESTRATEGIA_RANDOM,
) -> dict:
    """Treina e avalia o modelo de regressão de severidade de risco."""
    if estrategia_validacao not in ESTRATEGIAS_VALIDACAO:
        raise ValueError("estrategia_validacao deve ser 'random' ou 'temporal'.")

    df = df.copy()

    df["severidade_real"] = (
        df["status_transacao"].map(MAPA_SEVERIDADE_STATUS).fillna(SEVERIDADE_PADRAO)
    )

    X = df[FEATURES_REGRESSAO].fillna(0)
    y = df["severidade_real"]

    if estrategia_validacao == ESTRATEGIA_TEMPORAL:
        indices_treino, indices_teste = dividir_holdout_temporal(
            df,
            test_size=0.25,
        )

        X_train = X.iloc[indices_treino]
        X_test = X.iloc[indices_teste]
        y_train = y.iloc[indices_treino]
        y_test = y.iloc[indices_teste]

    else:
        X_train, X_test, y_train, y_test = train_test_split(
            X,
            y,
            test_size=0.25,
            random_state=42,
        )

    modelo = LinearRegression()
    modelo.fit(X_train, y_train)

    y_pred_test = modelo.predict(X_test)

    r2 = r2_score(y_test, y_pred_test)
    mae = mean_absolute_error(y_test, y_pred_test)
    rmse = float(
        np.sqrt(
            mean_squared_error(
                y_test,
                y_pred_test,
            )
        )
    )

    cv_scores = []

    if estrategia_validacao == ESTRATEGIA_TEMPORAL:
        folds_temporais = criar_folds_temporais(
            df,
            n_splits=5,
        )

        folds_validos = [
            (indices_treino, indices_teste)
            for indices_treino, indices_teste in folds_temporais
            if len(indices_treino) >= 2 and len(indices_teste) >= 2
        ]

        if folds_validos:
            cv_scores = cross_val_score(
                modelo,
                X,
                y,
                cv=folds_validos,
                scoring="r2",
            ).tolist()

    else:
        cv_scores = cross_val_score(
            modelo,
            X,
            y,
            cv=5,
            scoring="r2",
        ).tolist()

    score_risco_predito = modelo.predict(X).clip(0, 100)

    return {
        "modelo": modelo,
        "score_risco_predito": score_risco_predito,
        "metricas": {
            "estrategia_validacao": estrategia_validacao,
            "n_treino": len(X_train),
            "n_teste": len(X_test),
            "r2_teste": float(r2),
            "mae_teste": float(mae),
            "rmse_teste": float(rmse),
            "r2_cv_media": (float(np.mean(cv_scores)) if cv_scores else None),
            "r2_cv_desvio": (float(np.std(cv_scores)) if cv_scores else None),
        },
    }
