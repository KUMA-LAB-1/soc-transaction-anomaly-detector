import numpy as np
import pandas as pd
from sklearn.metrics import f1_score, precision_score, recall_score, roc_auc_score


def avaliar_detector(
    y_real: pd.Series,
    predicao_original: np.ndarray,
    score_original: np.ndarray,
) -> dict:
    """Calcula métricas de um detector de anomalia.

    Os detectores usam:
    - 1 para observação normal;
    - -1 para anomalia.

    Para comparação com status_transacao, as anomalias são convertidas para 1.
    """
    y_pred = (predicao_original == -1).astype(int)

    precision = precision_score(y_real, y_pred, zero_division=0)
    recall = recall_score(y_real, y_pred, zero_division=0)
    f1 = f1_score(y_real, y_pred, zero_division=0)

    auc = None
    if y_real.nunique() > 1 and len(np.unique(score_original)) > 1:
        auc = float(roc_auc_score(y_real, -score_original))

    return {
        "y_pred": y_pred,
        "precision": float(precision),
        "recall": float(recall),
        "f1": float(f1),
        "roc_auc": auc,
    }


def selecionar_melhor_detector_benchmark(
    resultados_validos: list[dict],
) -> dict:
    """Seleciona o melhor detector no benchmark retrospectivo.

    Critérios, nesta ordem:
    1. maior F1-score;
    2. maior recall;
    3. maior precision;
    4. menor tempo de execução.

    A seleção representa desempenho retrospectivo contra os labels
    disponíveis e não constitui, por si só, promoção operacional.
    """

    if not resultados_validos:
        raise RuntimeError(
            "Nenhum detector de anomalia conseguiu concluir o treinamento."
        )

    return max(
        resultados_validos,
        key=lambda resultado: (
            resultado["f1_vs_status_real"],
            resultado["recall_vs_status_real"],
            resultado["precision_vs_status_real"],
            -resultado["tempo_segundos"],
        ),
    )


def selecionar_melhor_detector(
    resultados_validos: list[dict],
) -> dict:
    """Compatibilidade com a API anterior."""
    return selecionar_melhor_detector_benchmark(resultados_validos)
