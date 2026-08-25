import numpy as np
import pandas as pd
import pytest

from src.models.evaluation import (
    avaliar_detector,
    selecionar_melhor_detector,
    selecionar_melhor_detector_benchmark,
)


def test_avaliar_detector_perfeito():
    y_real = pd.Series([0, 0, 1, 1])

    predicao_original = np.array([1, 1, -1, -1])
    score_original = np.array([0.8, 0.5, -0.4, -0.7])

    resultado = avaliar_detector(
        y_real=y_real,
        predicao_original=predicao_original,
        score_original=score_original,
    )

    assert resultado["precision"] == 1.0
    assert resultado["recall"] == 1.0
    assert resultado["f1"] == 1.0
    assert resultado["roc_auc"] == 1.0
    assert resultado["y_pred"].tolist() == [0, 0, 1, 1]


def test_selecionar_melhor_detector_benchmark_prioriza_f1():
    resultados = [
        {
            "modelo": "modelo_a",
            "f1_vs_status_real": 0.70,
            "recall_vs_status_real": 0.90,
            "precision_vs_status_real": 0.90,
            "tempo_segundos": 0.1,
        },
        {
            "modelo": "modelo_b",
            "f1_vs_status_real": 0.80,
            "recall_vs_status_real": 0.60,
            "precision_vs_status_real": 0.70,
            "tempo_segundos": 0.5,
        },
    ]

    melhor = selecionar_melhor_detector_benchmark(resultados)

    assert melhor["modelo"] == "modelo_b"


def test_selecionar_melhor_detector_benchmark_desempata_por_tempo():
    resultados = [
        {
            "modelo": "lento",
            "f1_vs_status_real": 0.80,
            "recall_vs_status_real": 0.70,
            "precision_vs_status_real": 0.90,
            "tempo_segundos": 0.5,
        },
        {
            "modelo": "rapido",
            "f1_vs_status_real": 0.80,
            "recall_vs_status_real": 0.70,
            "precision_vs_status_real": 0.90,
            "tempo_segundos": 0.1,
        },
    ]

    melhor = selecionar_melhor_detector_benchmark(resultados)

    assert melhor["modelo"] == "rapido"


def test_selecionar_melhor_detector_benchmark_rejeita_lista_vazia():
    with pytest.raises(RuntimeError):
        selecionar_melhor_detector_benchmark([])


def test_selecionar_melhor_detector_mantem_compatibilidade():
    resultados = [
        {
            "modelo": "modelo_a",
            "f1_vs_status_real": 0.70,
            "recall_vs_status_real": 0.80,
            "precision_vs_status_real": 0.90,
            "tempo_segundos": 0.1,
        },
        {
            "modelo": "modelo_b",
            "f1_vs_status_real": 0.90,
            "recall_vs_status_real": 0.70,
            "precision_vs_status_real": 0.80,
            "tempo_segundos": 0.2,
        },
    ]

    antigo = selecionar_melhor_detector(resultados)
    benchmark = selecionar_melhor_detector_benchmark(resultados)

    assert antigo == benchmark
