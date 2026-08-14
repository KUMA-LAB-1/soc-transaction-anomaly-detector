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

CONTAMINATION_TETO_PRATICO = 0.15

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


def executar_detectores_anomalia(df: pd.DataFrame) -> dict:
    """Executa os detectores de anomalia usando uma configuração comum."""
    taxa_suspeita_real = df["status_transacao"].isin(STATUS_SUSPEITOS).mean()

    contamination_estimado = float(np.clip(taxa_suspeita_real, 0.02, 0.30))
    contamination = min(
        contamination_estimado,
        CONTAMINATION_TETO_PRATICO,
    )

    features = [coluna for coluna in FEATURES_ANOMALIA if coluna in df.columns]

    X = df[features].fillna(0).astype(float)

    y_real = df["status_transacao"].isin(STATUS_SUSPEITOS).astype(int)

    n_vizinhos = max(5, min(35, len(X) - 1))

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
            modelo.fit(X)

            predicao_original = modelo.predict(X)
            score_original = modelo.decision_function(X)

            segundos = time.perf_counter() - inicio

            avaliacao = avaliar_detector(
                y_real=y_real,
                predicao_original=predicao_original,
                score_original=score_original,
            )

            resultado = {
                "modelo": nome,
                "status": "ok",
                "features": features,
                "contamination_estimado": contamination_estimado,
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
                    "status_transacao foi usado somente para auditoria comparativa."
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
        "taxa_suspeita_real": float(taxa_suspeita_real),
        "contamination_estimado": contamination_estimado,
        "contamination": contamination,
    }
