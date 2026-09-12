from datetime import datetime

import numpy as np
import pandas as pd
import pytest

from src.models.classification_benchmark import (
    _align_truth_to_evaluation,
    run_synthetic_classification_benchmark,
)
from src.synthetic.benchmark_experiment import (
    build_canonical_generation_config,
    build_canonical_label_policy,
    build_canonical_misturas,
)
from src.synthetic.dataset import (
    generate_synthetic_dataset_v3,
)
from src.synthetic.firewall import (
    projetar_ground_truth as projetar_ground_truth_real,
)
from src.synthetic.label_policy import (
    STATUS_SUSPEITO,
    OperationalLabelPolicy,
)


def test_classification_benchmark_usa_holdout_temporal_com_baseline_decision_tree():
    dataset = generate_synthetic_dataset_v3(
        seed=1,
        quantidade=200,
        inicio=datetime(2026, 1, 1),
        fim=datetime(2026, 1, 8),
        misturas=build_canonical_misturas(),
        label_policy=build_canonical_label_policy(),
        generation_config=build_canonical_generation_config(),
    )

    result = run_synthetic_classification_benchmark(
        dataset,
    )

    assert result.validation_strategy == "temporal"

    assert result.n_train > 0
    assert result.n_evaluation > 0

    assert result.n_train + result.n_evaluation == len(dataset.records)

    assert result.max_train_timestamp < result.min_evaluation_timestamp

    assert len(result.candidates) == 1

    baseline = result.candidates[0]

    assert baseline.model == "decision_tree"
    assert baseline.status == "ok"


def test_classification_benchmark_avalia_truth_separada_e_alinhada_por_id(
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

    assert all(
        (record.operational_labels["status_transacao"] == STATUS_SUSPEITO)
        != record.truth.is_suspicious
        for record in dataset.records
    )

    def fake_train(
        features,
        *,
        estrategia_validacao,
        indices_treino,
        indices_teste,
    ):
        assert estrategia_validacao == "temporal"
        assert indices_treino is not None
        assert indices_teste is not None

        forbidden_truth_columns = {
            "scenario",
            "is_suspicious",
            "attack_profile",
            "expected_mitre_techniques",
            "severity_score",
            "event_intensity",
        }

        assert forbidden_truth_columns.isdisjoint(features.columns)

        probabilities = np.array(
            [
                1.0 if truth_by_id[transaction_id] else 0.0
                for transaction_id in features["id_transacao"]
            ],
            dtype=float,
        )

        return {
            "proba_suspeita": probabilities,
        }

    def reversed_truth(records):
        return projetar_ground_truth_real(records).iloc[::-1].reset_index(drop=True)

    monkeypatch.setattr(
        "src.models.classification_benchmark.treinar_classificador_triagem",
        fake_train,
    )

    monkeypatch.setattr(
        "src.models.classification_benchmark.projetar_ground_truth",
        reversed_truth,
        raising=False,
    )

    result = run_synthetic_classification_benchmark(
        dataset,
    )

    candidate = result.candidates[0]

    assert candidate.precision == 1.0
    assert candidate.recall == 1.0
    assert candidate.f1 == 1.0
    assert candidate.roc_auc == 1.0

    assert candidate.false_positives == 0
    assert candidate.false_negatives == 0


def test_classification_benchmark_falha_quando_truth_esta_ausente():
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


def test_classification_benchmark_entrega_mesmo_holdout_ao_classificador(
    monkeypatch,
):
    dataset = generate_synthetic_dataset_v3(
        seed=1,
        quantidade=200,
        inicio=datetime(2026, 1, 1),
        fim=datetime(2026, 1, 8),
        misturas=build_canonical_misturas(),
        label_policy=build_canonical_label_policy(),
        generation_config=build_canonical_generation_config(),
    )

    expected_train = np.arange(
        0,
        150,
    )
    expected_evaluation = np.arange(
        150,
        200,
    )

    def fake_split(
        features,
        *,
        test_size,
    ):
        assert len(features) == 200
        assert test_size == 0.25

        return (
            expected_train,
            expected_evaluation,
        )

    def fake_train(
        features,
        *,
        estrategia_validacao,
        indices_treino,
        indices_teste,
    ):
        assert estrategia_validacao == "temporal"

        np.testing.assert_array_equal(
            indices_treino,
            expected_train,
        )
        np.testing.assert_array_equal(
            indices_teste,
            expected_evaluation,
        )

        return {
            "proba_suspeita": np.zeros(
                len(features),
                dtype=float,
            ),
        }

    monkeypatch.setattr(
        "src.models.classification_benchmark.dividir_holdout_temporal",
        fake_split,
    )

    monkeypatch.setattr(
        "src.models.classification_benchmark.treinar_classificador_triagem",
        fake_train,
    )

    result = run_synthetic_classification_benchmark(
        dataset,
    )

    assert result.n_train == 150
    assert result.n_evaluation == 50
