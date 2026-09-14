from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    auc,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from ..features.engineering import criar_features
from ..synthetic.dataset import GeneratedSyntheticDataset
from ..synthetic.firewall import (
    projetar_dataset_modelagem,
    projetar_ground_truth,
)
from .classification import (
    ESTRATEGIA_TEMPORAL,
    criar_classificador_triagem,
    preparar_dados_classificacao,
)
from .validation import dividir_holdout_temporal


def criar_classificador_logistic_benchmark() -> Pipeline:
    """Cria o challenger LogisticRegression exclusivo do benchmark."""
    return Pipeline(
        steps=[
            (
                "scaler",
                StandardScaler(),
            ),
            (
                "classifier",
                LogisticRegression(
                    class_weight="balanced",
                    max_iter=1000,
                    random_state=42,
                ),
            ),
        ]
    )


def criar_classificador_random_forest_benchmark() -> RandomForestClassifier:
    """Cria o challenger RandomForest exclusivo do benchmark."""
    return RandomForestClassifier(
        n_estimators=100,
        max_depth=4,
        class_weight="balanced",
        random_state=42,
        n_jobs=1,
    )


@dataclass(frozen=True, slots=True)
class ClassificationBenchmarkExecution:
    probabilities: np.ndarray
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class ClassificationBenchmarkCandidate:
    model: str
    status: str
    precision: float
    recall: float
    f1: float
    roc_auc: float | None
    pr_auc: float | None
    positive_count: int
    positive_rate: float
    false_positives: int
    false_negatives: int
    elapsed_seconds: float


@dataclass(frozen=True, slots=True)
class SyntheticClassificationBenchmarkResult:
    validation_strategy: str
    n_train: int
    n_evaluation: int
    max_train_timestamp: pd.Timestamp
    min_evaluation_timestamp: pd.Timestamp
    candidates: tuple[ClassificationBenchmarkCandidate, ...]


def _prepare_modeling_dataset(
    dataset: GeneratedSyntheticDataset,
) -> pd.DataFrame:
    modeling = projetar_dataset_modelagem(
        dataset.records,
    )

    modeling["hora"] = pd.to_datetime(
        modeling["data_hora_transacao"],
    ).dt.hour

    return criar_features(
        modeling.copy(),
    )


def _align_truth_to_evaluation(
    features: pd.DataFrame,
    truth: pd.DataFrame,
    evaluation_indices: np.ndarray,
) -> pd.Series:
    evaluation_ids = features.iloc[evaluation_indices][["id_transacao"]].copy()

    aligned = evaluation_ids.merge(
        truth[
            [
                "id_transacao",
                "is_suspicious",
            ]
        ],
        on="id_transacao",
        how="left",
        sort=False,
        validate="one_to_one",
    )

    if aligned["is_suspicious"].isna().any():
        raise RuntimeError(
            "Ground truth ausente para registros da janela de avaliacao."
        )

    return aligned["is_suspicious"].astype(int)


def _execute_classification_benchmark_model(
    *,
    model_factory,
    X: pd.DataFrame,
    y: pd.Series,
    train_indices: np.ndarray,
) -> ClassificationBenchmarkExecution:
    """Executa fit e inferencia sob uma fronteira temporal comparavel."""
    model = model_factory()

    training_started = perf_counter()

    model.fit(
        X.iloc[train_indices],
        y.iloc[train_indices],
    )

    probability_matrix = np.asarray(
        model.predict_proba(X),
        dtype=float,
    )

    elapsed_seconds = perf_counter() - training_started

    classes = np.asarray(
        model.classes_,
    )

    positive_positions = np.flatnonzero(
        classes == 1,
    )

    if positive_positions.size == 0:
        probabilities = np.zeros(
            len(X),
            dtype=float,
        )
    else:
        positive_index = int(positive_positions[0])

        probabilities = probability_matrix[
            :,
            positive_index,
        ]

    return ClassificationBenchmarkExecution(
        probabilities=np.asarray(
            probabilities,
            dtype=float,
        ),
        elapsed_seconds=elapsed_seconds,
    )


def _build_classification_candidate(
    *,
    model: str,
    probabilities: np.ndarray,
    evaluation_indices: np.ndarray,
    truth: pd.Series,
    elapsed_seconds: float,
) -> ClassificationBenchmarkCandidate:
    evaluation_probabilities = np.asarray(
        probabilities,
        dtype=float,
    )[evaluation_indices]

    y_true = truth.to_numpy(
        dtype=int,
    )

    y_pred = (evaluation_probabilities >= 0.5).astype(int)

    has_both_classes = np.unique(y_true).size > 1

    roc_auc = (
        float(
            roc_auc_score(
                y_true,
                evaluation_probabilities,
            )
        )
        if has_both_classes
        else None
    )

    if has_both_classes:
        precision_curve, recall_curve, _ = precision_recall_curve(
            y_true,
            evaluation_probabilities,
        )
        pr_auc = float(
            auc(
                recall_curve,
                precision_curve,
            )
        )
    else:
        pr_auc = None

    positive_count = int(y_pred.sum())
    positive_rate = float(positive_count / len(y_pred))

    false_positives = int(((y_pred == 1) & (y_true == 0)).sum())

    false_negatives = int(((y_pred == 0) & (y_true == 1)).sum())

    return ClassificationBenchmarkCandidate(
        model=model,
        status="ok",
        precision=float(
            precision_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        recall=float(
            recall_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        f1=float(
            f1_score(
                y_true,
                y_pred,
                zero_division=0,
            )
        ),
        roc_auc=roc_auc,
        pr_auc=pr_auc,
        positive_count=positive_count,
        positive_rate=positive_rate,
        false_positives=false_positives,
        false_negatives=false_negatives,
        elapsed_seconds=elapsed_seconds,
    )


def run_synthetic_classification_benchmark(
    dataset: GeneratedSyntheticDataset,
) -> SyntheticClassificationBenchmarkResult:
    features = _prepare_modeling_dataset(
        dataset,
    )

    truth = projetar_ground_truth(
        dataset.records,
    )

    train_indices, evaluation_indices = dividir_holdout_temporal(
        features,
        test_size=0.25,
    )

    prepared = preparar_dados_classificacao(
        features,
    )

    aligned_truth = _align_truth_to_evaluation(
        features,
        truth,
        evaluation_indices,
    )

    candidate_specs = (
        (
            "decision_tree",
            criar_classificador_triagem,
        ),
        (
            "logistic_regression",
            criar_classificador_logistic_benchmark,
        ),
        (
            "random_forest",
            criar_classificador_random_forest_benchmark,
        ),
    )

    candidates = []

    for model_name, model_factory in candidate_specs:
        execution = _execute_classification_benchmark_model(
            model_factory=model_factory,
            X=prepared.X,
            y=prepared.y,
            train_indices=train_indices,
        )

        candidates.append(
            _build_classification_candidate(
                model=model_name,
                probabilities=execution.probabilities,
                evaluation_indices=evaluation_indices,
                truth=aligned_truth,
                elapsed_seconds=execution.elapsed_seconds,
            )
        )

    timestamps = pd.to_datetime(
        features["data_hora_transacao"],
    )

    return SyntheticClassificationBenchmarkResult(
        validation_strategy=ESTRATEGIA_TEMPORAL,
        n_train=len(train_indices),
        n_evaluation=len(evaluation_indices),
        max_train_timestamp=timestamps.iloc[train_indices].max(),
        min_evaluation_timestamp=timestamps.iloc[evaluation_indices].min(),
        candidates=tuple(candidates),
    )
