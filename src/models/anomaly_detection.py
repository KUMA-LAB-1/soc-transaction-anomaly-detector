import time

import numpy as np
import pandas as pd
from sklearn.covariance import EllipticEnvelope
from sklearn.ensemble import IsolationForest
from sklearn.neighbors import LocalOutlierFactor
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.svm import OneClassSVM

from .evaluation import avaliar_detector
from .validation import dividir_holdout_temporal

CONTAMINATION_PISO_PRATICO = 0.02
CONTAMINATION_TETO_PRATICO = 0.15
CONTAMINATION_PADRAO = CONTAMINATION_TETO_PRATICO

ESTRATEGIA_IN_SAMPLE = "in_sample"
ESTRATEGIA_TEMPORAL = "temporal"

ESTRATEGIAS_VALIDACAO = {
    ESTRATEGIA_IN_SAMPLE,
    ESTRATEGIA_TEMPORAL,
}

FEATURES_ANOMALIA = [
    "valor_transacao",
    "hora",
    "zscore_valor_cliente",
    "qtd_transacoes_anteriores",
    "falhas_login_recentes",
    "dispositivo_novo_flag",
    "alteracao_limite_flag",
    "mudanca_localizacao_flag",
]

STATUS_SUSPEITOS = [
    "Em Análise",
    "Bloqueada por Suspeita",
]


def executar_detectores_anomalia(
    df: pd.DataFrame,
    *,
    estrategia_validacao: str = ESTRATEGIA_IN_SAMPLE,
    contamination: float = CONTAMINATION_PADRAO,
) -> dict:
    """Executa os detectores de anomalia usando uma configuração comum."""
    if estrategia_validacao not in ESTRATEGIAS_VALIDACAO:
        raise ValueError("estrategia_validacao deve ser 'in_sample' ou 'temporal'.")

    contamination = float(contamination)

    if (
        not np.isfinite(contamination)
        or contamination < CONTAMINATION_PISO_PRATICO
        or contamination > CONTAMINATION_TETO_PRATICO
    ):
        raise ValueError("contamination deve estar entre 0.02 e 0.15.")

    features = [coluna for coluna in FEATURES_ANOMALIA if coluna in df.columns]

    X = df[features].fillna(0).astype(float)

    y_real = df["status_transacao"].isin(STATUS_SUSPEITOS).astype(int)

    taxa_suspeita_real = float(y_real.mean())

    if estrategia_validacao == ESTRATEGIA_TEMPORAL:
        indices_treino, indices_avaliacao = dividir_holdout_temporal(
            df,
            test_size=0.25,
        )

        X_treino = X.iloc[indices_treino]
        X_avaliacao = X.iloc[indices_avaliacao]

        y_avaliacao = y_real.iloc[indices_avaliacao]

    else:
        indices_treino = np.arange(len(df))
        indices_avaliacao = np.arange(len(df))

        X_treino = X
        X_avaliacao = X

        y_avaliacao = y_real

    n_vizinhos = max(
        5,
        min(
            35,
            len(X_treino) - 1,
        ),
    )

    detectores = {
        "isolation_forest": IsolationForest(
            contamination=contamination,
            n_estimators=300,
            random_state=42,
            n_jobs=-1,
        ),
        "local_outlier_factor": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "modelo",
                    LocalOutlierFactor(
                        n_neighbors=n_vizinhos,
                        contamination=contamination,
                        novelty=True,
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
        "one_class_svm": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "modelo",
                    OneClassSVM(
                        kernel="rbf",
                        gamma="scale",
                        nu=contamination,
                    ),
                ),
            ]
        ),
        "elliptic_envelope": Pipeline(
            [
                ("scaler", StandardScaler()),
                (
                    "modelo",
                    EllipticEnvelope(
                        contamination=contamination,
                        random_state=42,
                        support_fraction=None,
                    ),
                ),
            ]
        ),
    }

    resultados = []
    modelos = {}
    predicoes = {}

    for nome, modelo in detectores.items():
        inicio = time.perf_counter()

        try:
            modelo.fit(X_treino)

            predicao_original = modelo.predict(X_avaliacao)
            score_original = modelo.decision_function(X_avaliacao)
            segundos = time.perf_counter() - inicio

            avaliacao = avaliar_detector(
                y_real=y_avaliacao,
                predicao_original=predicao_original,
                score_original=score_original,
            )

            resultado = {
                "estrategia_validacao": estrategia_validacao,
                "n_treino": len(X_treino),
                "n_avaliacao": len(X_avaliacao),
                "modelo": nome,
                "status": "ok",
                "features": features,
                "contamination_configurado": contamination,
                "contamination_usado": contamination,
                "qtd_anomalias": int(avaliacao["y_pred"].sum()),
                "taxa_anomalias": float(avaliacao["y_pred"].mean()),
                "precision_vs_status_real": avaliacao["precision"],
                "recall_vs_status_real": avaliacao["recall"],
                "f1_vs_status_real": avaliacao["f1"],
                "roc_auc_score_anomalia": avaliacao["roc_auc"],
                "tempo_segundos": float(segundos),
                "nota": (
                    "Modelo não supervisionado/novelty detection. "
                    "status_transacao é usado somente para auditoria retrospectiva "
                    "e não configura os detectores."
                ),
            }

            resultados.append(resultado)
            modelos[nome] = modelo

            predicoes[nome] = {
                "predicao_original": predicao_original,
                "score_original": score_original,
            }

        except Exception as exc:
            segundos = time.perf_counter() - inicio

            resultados.append(
                {
                    "modelo": nome,
                    "status": "erro",
                    "erro": str(exc),
                    "tempo_segundos": float(segundos),
                }
            )

    return {
        "resultados": resultados,
        "modelos": modelos,
        "predicoes": predicoes,
        "estrategia_validacao": estrategia_validacao,
        "indices_treino": indices_treino,
        "indices_avaliacao": indices_avaliacao,
        "n_treino": len(X_treino),
        "n_avaliacao": len(X_avaliacao),
        "taxa_suspeita_real": float(taxa_suspeita_real),
        "contamination_configurado": contamination,
        "contamination": contamination,
    }
