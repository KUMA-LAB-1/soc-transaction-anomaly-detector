from __future__ import annotations

from dataclasses import dataclass

import numpy as np
import pandas as pd

from ..features.engineering import criar_features
from ..synthetic.dataset import GeneratedSyntheticDataset
from ..synthetic.firewall import (
    projetar_dataset_modelagem,
    projetar_ground_truth,
)
from .anomaly_detection import (
    ESTRATEGIA_TEMPORAL,
    executar_detectores_anomalia,
)
from .evaluation import avaliar_detector, chave_ranking_detector


@dataclass(frozen=True, slots=True)
class DetectorBenchmarkEntry:
    detector: str
    status: str
    precision: float | None
    recall: float | None
    f1: float | None
    roc_auc: float | None
    false_positives: int | None
    false_negatives: int | None
    alert_count: int | None
    alert_rate: float | None
    elapsed_seconds: float
    error: str | None = None


@dataclass(frozen=True, slots=True)
class SyntheticDetectorBenchmarkResult:
    validation_strategy: str
    n_train: int
    n_evaluation: int
    max_train_timestamp: pd.Timestamp
    min_evaluation_timestamp: pd.Timestamp
    detectors: tuple[DetectorBenchmarkEntry, ...]
    benchmark_champion: str | None


def _prepare_modeling_dataset(
    dataset: GeneratedSyntheticDataset,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    modeling = projetar_dataset_modelagem(
        dataset.records,
    )
    truth = projetar_ground_truth(
        dataset.records,
    )

    modeling["hora"] = pd.to_datetime(modeling["data_hora_transacao"]).dt.hour

    features = criar_features(modeling.copy())

    return features, truth


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


def _build_detector_entry(
    result: dict,
    predictions: dict | None,
    truth: pd.Series,
) -> DetectorBenchmarkEntry:
    if result["status"] != "ok":
        return DetectorBenchmarkEntry(
            detector=result["modelo"],
            status="erro",
            precision=None,
            recall=None,
            f1=None,
            roc_auc=None,
            false_positives=None,
            false_negatives=None,
            alert_count=None,
            alert_rate=None,
            elapsed_seconds=float(result["tempo_segundos"]),
            error=result.get("erro"),
        )

    if predictions is None:
        raise RuntimeError("Detector concluido sem predicoes associadas.")

    evaluation = avaliar_detector(
        y_real=truth,
        predicao_original=predictions["predicao_original"],
        score_original=predictions["score_original"],
    )

    y_true = truth.to_numpy(
        dtype=int,
    )
    y_pred = evaluation["y_pred"]

    false_positives = int(((y_pred == 1) & (y_true == 0)).sum())
    false_negatives = int(((y_pred == 0) & (y_true == 1)).sum())

    alert_count = int(y_pred.sum())
    alert_rate = float(y_pred.mean())

    return DetectorBenchmarkEntry(
        detector=result["modelo"],
        status="ok",
        precision=evaluation["precision"],
        recall=evaluation["recall"],
        f1=evaluation["f1"],
        roc_auc=evaluation["roc_auc"],
        false_positives=false_positives,
        false_negatives=false_negatives,
        alert_count=alert_count,
        alert_rate=alert_rate,
        elapsed_seconds=float(result["tempo_segundos"]),
    )


def selecionar_campeao_benchmark_truth(
    detectors: tuple[DetectorBenchmarkEntry, ...],
) -> DetectorBenchmarkEntry | None:
    validos = tuple(detector for detector in detectors if detector.status == "ok")

    if not validos:
        return None

    return max(
        validos,
        key=lambda detector: chave_ranking_detector(
            f1=detector.f1,
            recall=detector.recall,
            precision=detector.precision,
            tempo_segundos=detector.elapsed_seconds,
        ),
    )


def run_synthetic_detector_benchmark(
    dataset: GeneratedSyntheticDataset,
    *,
    contamination: float,
) -> SyntheticDetectorBenchmarkResult:
    features, truth = _prepare_modeling_dataset(dataset)

    execution = executar_detectores_anomalia(
        features,
        estrategia_validacao=ESTRATEGIA_TEMPORAL,
        contamination=contamination,
    )

    train_indices = execution["indices_treino"]
    evaluation_indices = execution["indices_avaliacao"]

    aligned_truth = _align_truth_to_evaluation(
        features,
        truth,
        evaluation_indices,
    )

    timestamps = pd.to_datetime(features["data_hora_transacao"])

    detector_entries = tuple(
        _build_detector_entry(
            result,
            execution["predicoes"].get(result["modelo"]),
            aligned_truth,
        )
        for result in execution["resultados"]
    )

    benchmark_champion = selecionar_campeao_benchmark_truth(detector_entries)

    return SyntheticDetectorBenchmarkResult(
        validation_strategy=execution["estrategia_validacao"],
        n_train=execution["n_treino"],
        n_evaluation=execution["n_avaliacao"],
        max_train_timestamp=timestamps.iloc[train_indices].max(),
        min_evaluation_timestamp=timestamps.iloc[evaluation_indices].min(),
        detectors=detector_entries,
        benchmark_champion=(
            benchmark_champion.detector if benchmark_champion is not None else None
        ),
    )
