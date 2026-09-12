from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.models.detector_benchmark import (
    DetectorBenchmarkEntry,
    _align_truth_to_evaluation,
    _build_detector_entry,
    run_synthetic_detector_benchmark,
    selecionar_campeao_benchmark_truth,
)
from src.synthetic.benchmark_experiment import (
    build_canonical_generation_config,
    build_canonical_label_policy,
    build_canonical_misturas,
)
from src.synthetic.dataset import generate_synthetic_dataset_v3
from src.synthetic.label_policy import (
    STATUS_NORMAL,
    OperationalLabelPolicy,
)


def test_detector_benchmark_usa_truth_separada_e_holdout_temporal():
    dataset = generate_synthetic_dataset_v3(
        seed=1,
        quantidade=200,
        inicio=datetime(2026, 1, 1),
        fim=datetime(2026, 1, 8),
        misturas=build_canonical_misturas(),
        label_policy=build_canonical_label_policy(),
        generation_config=build_canonical_generation_config(),
    )

    result = run_synthetic_detector_benchmark(
        dataset,
        contamination=0.15,
    )

    assert result.validation_strategy == "temporal"
    assert result.n_train > 0
    assert result.n_evaluation > 0
    assert result.max_train_timestamp < result.min_evaluation_timestamp

    assert {entry.detector for entry in result.detectors} == {
        "isolation_forest",
        "local_outlier_factor",
        "one_class_svm",
        "elliptic_envelope",
    }

    for entry in result.detectors:
        assert entry.status == "ok"
        assert 0.0 <= entry.precision <= 1.0
        assert 0.0 <= entry.recall <= 1.0
        assert 0.0 <= entry.f1 <= 1.0
        assert entry.false_positives >= 0
        assert entry.false_negatives >= 0
        assert entry.alert_count >= 0
        assert 0.0 <= entry.alert_rate <= 1.0
        assert entry.elapsed_seconds >= 0.0


def test_detector_benchmark_nao_usa_label_operacional_como_truth(
    monkeypatch,
):
    dataset = generate_synthetic_dataset_v3(
        seed=1,
        quantidade=200,
        inicio=datetime(2026, 1, 1),
        fim=datetime(2026, 1, 8),
        misturas=build_canonical_misturas(),
        label_policy=OperationalLabelPolicy(
            probabilidade_falso_positivo=1.0,
            probabilidade_falso_negativo=1.0,
        ),
        generation_config=build_canonical_generation_config(),
    )

    truth_by_id = {
        record.observables["id_transacao"]: record.truth.is_suspicious
        for record in dataset.records
    }

    operational_by_id = {
        record.observables["id_transacao"]: record.operational_labels[
            "status_transacao"
        ]
        for record in dataset.records
    }

    assert all(
        (operational_by_id[record.observables["id_transacao"]] == STATUS_NORMAL)
        == record.truth.is_suspicious
        for record in dataset.records
    )

    def fake_execute(
        features,
        *,
        estrategia_validacao,
        contamination,
    ):
        train_indices = np.arange(150)
        evaluation_indices = np.arange(
            150,
            len(features),
        )

        evaluation_ids = features.iloc[evaluation_indices]["id_transacao"]

        truth = np.array(
            [truth_by_id[transaction_id] for transaction_id in evaluation_ids],
            dtype=bool,
        )

        predictions = np.where(
            truth,
            -1,
            1,
        )

        scores = np.where(
            truth,
            -1.0,
            1.0,
        )

        return {
            "resultados": [
                {
                    "modelo": "controlled_detector",
                    "status": "ok",
                    "precision_vs_status_real": 0.0,
                    "recall_vs_status_real": 0.0,
                    "f1_vs_status_real": 0.0,
                    "tempo_segundos": 0.001,
                }
            ],
            "modelos": {},
            "predicoes": {
                "controlled_detector": {
                    "predicao_original": predictions,
                    "score_original": scores,
                }
            },
            "estrategia_validacao": estrategia_validacao,
            "indices_treino": train_indices,
            "indices_avaliacao": evaluation_indices,
            "n_treino": len(train_indices),
            "n_avaliacao": len(evaluation_indices),
            "taxa_suspeita_real": 0.0,
            "contamination_configurado": contamination,
            "contamination": contamination,
        }

    monkeypatch.setattr(
        "src.models.detector_benchmark.executar_detectores_anomalia",
        fake_execute,
    )

    result = run_synthetic_detector_benchmark(
        dataset,
        contamination=0.15,
    )

    assert len(result.detectors) == 1
    assert result.benchmark_champion == "controlled_detector"

    detector = result.detectors[0]

    assert detector.detector == "controlled_detector"
    assert detector.precision == 1.0
    assert detector.recall == 1.0
    assert detector.f1 == 1.0
    assert detector.false_positives == 0
    assert detector.false_negatives == 0


def test_detector_benchmark_falha_quando_truth_esta_ausente():
    features = pd.DataFrame(
        {
            "id_transacao": [
                "tx-1",
                "tx-2",
            ]
        }
    )
    truth = pd.DataFrame(
        {
            "id_transacao": [
                "tx-1",
            ],
            "is_suspicious": [
                False,
            ],
        }
    )

    with pytest.raises(
        RuntimeError,
        match="Ground truth ausente",
    ):
        _align_truth_to_evaluation(
            features,
            truth,
            np.array([1]),
        )


def test_detector_benchmark_preserva_erro_do_detector():
    entry = _build_detector_entry(
        {
            "modelo": "broken_detector",
            "status": "erro",
            "erro": "falha simulada",
            "tempo_segundos": 0.25,
        },
        predictions=None,
        truth=pd.Series(
            [0],
            dtype=int,
        ),
    )

    assert entry.detector == "broken_detector"
    assert entry.status == "erro"
    assert entry.error == "falha simulada"
    assert entry.precision is None
    assert entry.recall is None
    assert entry.f1 is None
    assert entry.roc_auc is None
    assert entry.false_positives is None
    assert entry.false_negatives is None
    assert entry.alert_count is None
    assert entry.alert_rate is None
    assert entry.elapsed_seconds == pytest.approx(0.25)


def test_detector_benchmark_falha_se_detector_ok_nao_tem_predicoes():
    with pytest.raises(
        RuntimeError,
        match="Detector concluido sem predicoes",
    ):
        _build_detector_entry(
            {
                "modelo": "invalid_detector",
                "status": "ok",
                "tempo_segundos": 0.01,
            },
            predictions=None,
            truth=pd.Series(
                [0],
                dtype=int,
            ),
        )


def test_selecionar_campeao_benchmark_truth_ignora_erros():
    erro = DetectorBenchmarkEntry(
        detector="detector_com_erro",
        status="erro",
        precision=None,
        recall=None,
        f1=None,
        roc_auc=None,
        false_positives=None,
        false_negatives=None,
        alert_count=None,
        alert_rate=None,
        elapsed_seconds=0.001,
        error="falha simulada",
    )

    lento = DetectorBenchmarkEntry(
        detector="detector_lento",
        status="ok",
        precision=0.90,
        recall=0.70,
        f1=0.80,
        roc_auc=0.85,
        false_positives=2,
        false_negatives=3,
        alert_count=10,
        alert_rate=0.20,
        elapsed_seconds=0.50,
    )

    rapido = DetectorBenchmarkEntry(
        detector="detector_rapido",
        status="ok",
        precision=0.90,
        recall=0.70,
        f1=0.80,
        roc_auc=0.85,
        false_positives=2,
        false_negatives=3,
        alert_count=10,
        alert_rate=0.20,
        elapsed_seconds=0.10,
    )

    campeao = selecionar_campeao_benchmark_truth(
        (
            erro,
            lento,
            rapido,
        )
    )

    assert campeao is rapido

    assert selecionar_campeao_benchmark_truth((erro,)) is None
