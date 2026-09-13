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

    assert tuple(candidate.model for candidate in result.candidates) == (
        "decision_tree",
        "logistic_regression",
    )

    baseline = result.candidates[0]

    assert baseline.model == "decision_tree"
    assert baseline.status == "ok"


def test_classification_benchmark_avalia_truth_separada_e_alinhada_por_id(
    monkeypatch,
):
    from src.models.classification_benchmark import (
        ClassificationBenchmarkExecution,
    )

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

    ordered_ids = [record.observables["id_transacao"] for record in dataset.records]

    assert all(
        (record.operational_labels["status_transacao"] == STATUS_SUSPEITO)
        != record.truth.is_suspicious
        for record in dataset.records
    )

    def fake_executor(
        *,
        model_factory,
        X,
        y,
        train_indices,
    ):
        assert len(X) == len(ordered_ids)
        assert len(y) == len(ordered_ids)
        assert train_indices.size > 0

        forbidden_truth_columns = {
            "scenario",
            "is_suspicious",
            "attack_profile",
            "expected_mitre_techniques",
            "severity_score",
            "event_intensity",
        }

        assert forbidden_truth_columns.isdisjoint(X.columns)

        probabilities = np.array(
            [
                1.0 if truth_by_id[transaction_id] else 0.0
                for transaction_id in ordered_ids
            ],
            dtype=float,
        )

        return ClassificationBenchmarkExecution(
            probabilities=probabilities,
            elapsed_seconds=0.0,
        )

    def reversed_truth(records):
        return projetar_ground_truth_real(records).iloc[::-1].reset_index(drop=True)

    monkeypatch.setattr(
        "src.models.classification_benchmark._execute_classification_benchmark_model",
        fake_executor,
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
    from src.models.classification_benchmark import (
        ClassificationBenchmarkExecution,
    )

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

    def fake_executor(
        *,
        model_factory,
        X,
        y,
        train_indices,
    ):
        assert len(X) == 200
        assert len(y) == 200

        np.testing.assert_array_equal(
            train_indices,
            expected_train,
        )

        return ClassificationBenchmarkExecution(
            probabilities=np.zeros(
                len(X),
                dtype=float,
            ),
            elapsed_seconds=0.0,
        )

    monkeypatch.setattr(
        "src.models.classification_benchmark.dividir_holdout_temporal",
        fake_split,
    )

    monkeypatch.setattr(
        "src.models.classification_benchmark._execute_classification_benchmark_model",
        fake_executor,
    )

    result = run_synthetic_classification_benchmark(
        dataset,
    )

    assert result.n_train == 150
    assert result.n_evaluation == 50


def test_classification_benchmark_expoe_pr_auc_e_taxa_de_positivos(
    monkeypatch,
):
    from src.models.classification_benchmark import (
        ClassificationBenchmarkExecution,
    )

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

    truth_by_id = {
        record.observables["id_transacao"]: record.truth.is_suspicious
        for record in dataset.records
    }

    ordered_ids = [record.observables["id_transacao"] for record in dataset.records]

    def fake_split(
        features,
        *,
        test_size,
    ):
        assert test_size == 0.25

        return (
            expected_train,
            expected_evaluation,
        )

    def fake_executor(
        *,
        model_factory,
        X,
        y,
        train_indices,
    ):
        np.testing.assert_array_equal(
            train_indices,
            expected_train,
        )

        probabilities = np.array(
            [
                1.0 if truth_by_id[transaction_id] else 0.0
                for transaction_id in ordered_ids
            ],
            dtype=float,
        )

        return ClassificationBenchmarkExecution(
            probabilities=probabilities,
            elapsed_seconds=0.0,
        )

    monkeypatch.setattr(
        "src.models.classification_benchmark.dividir_holdout_temporal",
        fake_split,
    )

    monkeypatch.setattr(
        "src.models.classification_benchmark._execute_classification_benchmark_model",
        fake_executor,
    )

    result = run_synthetic_classification_benchmark(
        dataset,
    )

    candidate = result.candidates[0]

    evaluation_ids = (
        projetar_ground_truth_real(dataset.records)
        .iloc[expected_evaluation]["id_transacao"]
        .tolist()
    )

    expected_positive_count = sum(
        truth_by_id[transaction_id] for transaction_id in evaluation_ids
    )

    assert candidate.pr_auc == 1.0
    assert candidate.positive_count == expected_positive_count
    assert candidate.positive_rate == pytest.approx(
        expected_positive_count / len(expected_evaluation)
    )


def test_classification_candidate_pr_auc_usa_area_da_curva_precision_recall():
    from src.models.classification_benchmark import (
        _build_classification_candidate,
    )

    probabilities = np.array(
        [
            0.9,
            0.8,
            0.7,
            0.1,
        ],
        dtype=float,
    )

    evaluation_indices = np.arange(
        0,
        4,
    )

    truth = pd.Series(
        [
            1,
            0,
            1,
            0,
        ],
        dtype=int,
    )

    candidate = _build_classification_candidate(
        model="decision_tree",
        probabilities=probabilities,
        evaluation_indices=evaluation_indices,
        truth=truth,
        elapsed_seconds=0.0,
    )

    assert candidate.pr_auc == pytest.approx(0.7916666666666666)


def test_classification_candidate_single_class_nao_expoe_auc_indefinida():
    from src.models.classification_benchmark import (
        _build_classification_candidate,
    )

    probabilities = np.array(
        [
            0.1,
            0.2,
            0.3,
            0.4,
        ],
        dtype=float,
    )

    evaluation_indices = np.arange(
        0,
        4,
    )

    truth = pd.Series(
        [
            0,
            0,
            0,
            0,
        ],
        dtype=int,
    )

    candidate = _build_classification_candidate(
        model="decision_tree",
        probabilities=probabilities,
        evaluation_indices=evaluation_indices,
        truth=truth,
        elapsed_seconds=0.0,
    )

    assert candidate.roc_auc is None
    assert candidate.pr_auc is None
    assert candidate.positive_count == 0
    assert candidate.positive_rate == 0.0


def test_classification_benchmark_expoe_tempo_decorrido_do_treino(
    monkeypatch,
):
    from src.models.classification_benchmark import (
        ClassificationBenchmarkExecution,
    )

    dataset = generate_synthetic_dataset_v3(
        seed=1,
        quantidade=200,
        inicio=datetime(2026, 1, 1),
        fim=datetime(2026, 1, 8),
        misturas=build_canonical_misturas(),
        label_policy=build_canonical_label_policy(),
        generation_config=build_canonical_generation_config(),
    )

    def fake_executor(
        *,
        model_factory,
        X,
        y,
        train_indices,
    ):
        assert len(X) == len(dataset.records)
        assert len(y) == len(dataset.records)
        assert train_indices.size > 0

        return ClassificationBenchmarkExecution(
            probabilities=np.zeros(
                len(X),
                dtype=float,
            ),
            elapsed_seconds=0.25,
        )

    monkeypatch.setattr(
        "src.models.classification_benchmark._execute_classification_benchmark_model",
        fake_executor,
    )

    result = run_synthetic_classification_benchmark(
        dataset,
    )

    candidate = result.candidates[0]

    assert candidate.elapsed_seconds == pytest.approx(0.25)


def test_classification_candidate_rejeita_elapsed_seconds_ausente():
    from src.models.classification_benchmark import (
        _build_classification_candidate,
    )

    with pytest.raises(
        TypeError,
        match="elapsed_seconds",
    ):
        _build_classification_candidate(
            model="decision_tree",
            probabilities=np.array(
                [
                    0.1,
                    0.9,
                ],
                dtype=float,
            ),
            evaluation_indices=np.arange(
                0,
                2,
            ),
            truth=pd.Series(
                [
                    0,
                    1,
                ],
                dtype=int,
            ),
        )


def test_classification_candidate_builder_aceita_identidade_do_modelo():
    from src.models.classification_benchmark import (
        _build_classification_candidate,
    )

    candidate = _build_classification_candidate(
        model="logistic_regression",
        probabilities=np.array(
            [
                0.1,
                0.9,
            ],
            dtype=float,
        ),
        evaluation_indices=np.arange(
            0,
            2,
        ),
        truth=pd.Series(
            [
                0,
                1,
            ],
            dtype=int,
        ),
        elapsed_seconds=0.25,
    )

    assert candidate.model == "logistic_regression"
    assert candidate.status == "ok"
    assert candidate.precision == 1.0
    assert candidate.recall == 1.0
    assert candidate.f1 == 1.0
    assert candidate.roc_auc == 1.0
    assert candidate.pr_auc == 1.0
    assert candidate.positive_count == 1
    assert candidate.positive_rate == pytest.approx(0.5)
    assert candidate.false_positives == 0
    assert candidate.false_negatives == 0
    assert candidate.elapsed_seconds == pytest.approx(0.25)


def test_classification_benchmark_executor_mede_fit_e_predict_proba_no_mesmo_contrato(
    monkeypatch,
):
    import src.models.classification_benchmark as classification_benchmark
    from src.models.classification_benchmark import (
        _execute_classification_benchmark_model,
    )

    events = []

    X = pd.DataFrame(
        {
            "feature_a": [
                1.0,
                2.0,
                3.0,
                4.0,
            ],
        },
        index=[
            10,
            20,
            30,
            40,
        ],
    )

    y = pd.Series(
        [
            0,
            1,
            0,
            1,
        ],
        index=X.index,
        dtype=int,
    )

    train_indices = np.array(
        [
            0,
            1,
        ],
        dtype=int,
    )

    class FakeClassifier:
        classes_ = np.array(
            [
                0,
                1,
            ],
            dtype=int,
        )

        def fit(
            self,
            X_train,
            y_train,
        ):
            events.append("fit")

            assert X_train.index.tolist() == [
                10,
                20,
            ]

            assert y_train.index.tolist() == [
                10,
                20,
            ]

            return self

        def predict_proba(
            self,
            X_full,
        ):
            events.append("predict_proba")

            assert X_full.index.tolist() == [
                10,
                20,
                30,
                40,
            ]

            positive = np.array(
                [
                    0.1,
                    0.8,
                    0.2,
                    0.9,
                ],
                dtype=float,
            )

            return np.column_stack(
                [
                    1.0 - positive,
                    positive,
                ]
            )

    def factory():
        events.append("factory")
        return FakeClassifier()

    clock_values = iter(
        [
            100.0,
            100.25,
        ]
    )

    def fake_clock():
        value = next(clock_values)

        events.append("clock_start" if value == 100.0 else "clock_stop")

        return value

    monkeypatch.setattr(
        classification_benchmark,
        "perf_counter",
        fake_clock,
    )

    execution = _execute_classification_benchmark_model(
        model_factory=factory,
        X=X,
        y=y,
        train_indices=train_indices,
    )

    np.testing.assert_allclose(
        execution.probabilities,
        np.array(
            [
                0.1,
                0.8,
                0.2,
                0.9,
            ],
            dtype=float,
        ),
    )

    assert execution.elapsed_seconds == pytest.approx(0.25)

    assert events == [
        "factory",
        "clock_start",
        "fit",
        "predict_proba",
        "clock_stop",
    ]


def test_classification_benchmark_executor_retorna_zero_sem_classe_positiva(
    monkeypatch,
):
    import src.models.classification_benchmark as classification_benchmark
    from src.models.classification_benchmark import (
        _execute_classification_benchmark_model,
    )

    X = pd.DataFrame(
        {
            "feature_a": [
                1.0,
                2.0,
                3.0,
            ],
        }
    )

    y = pd.Series(
        [
            0,
            0,
            0,
        ],
        dtype=int,
    )

    class FakeSingleClassClassifier:
        classes_ = np.array(
            [
                0,
            ],
            dtype=int,
        )

        def fit(
            self,
            X_train,
            y_train,
        ):
            assert len(X_train) == 2
            assert y_train.tolist() == [
                0,
                0,
            ]

            return self

        def predict_proba(
            self,
            X_full,
        ):
            return np.ones(
                (
                    len(X_full),
                    1,
                ),
                dtype=float,
            )

    clock_values = iter(
        [
            10.0,
            10.1,
        ]
    )

    monkeypatch.setattr(
        classification_benchmark,
        "perf_counter",
        lambda: next(clock_values),
    )

    execution = _execute_classification_benchmark_model(
        model_factory=FakeSingleClassClassifier,
        X=X,
        y=y,
        train_indices=np.array(
            [
                0,
                1,
            ],
            dtype=int,
        ),
    )

    np.testing.assert_array_equal(
        execution.probabilities,
        np.zeros(
            len(X),
            dtype=float,
        ),
    )

    assert execution.elapsed_seconds == pytest.approx(0.1)


def test_classification_benchmark_baseline_usa_executor_comparavel_em_vez_do_trainer_operacional(
    monkeypatch,
):
    import src.models.classification_benchmark as classification_benchmark
    from src.models.classification_benchmark import (
        ClassificationBenchmarkExecution,
    )

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
        dtype=int,
    )

    expected_evaluation = np.arange(
        150,
        200,
        dtype=int,
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

    def forbidden_operational_trainer(
        *args,
        **kwargs,
    ):
        raise AssertionError("benchmark nao deve usar treinar_classificador_triagem")

    executor_calls = []

    def fake_executor(
        *,
        model_factory,
        X,
        y,
        train_indices,
    ):
        assert model_factory.__name__ in {
            "criar_classificador_triagem",
            "criar_classificador_logistic_benchmark",
        }

        assert len(X) == 200
        assert len(y) == 200
        assert X.index.equals(y.index)

        np.testing.assert_array_equal(
            train_indices,
            expected_train,
        )

        executor_calls.append(
            {
                "factory_name": model_factory.__name__,
                "n_rows": len(X),
                "n_train": len(train_indices),
            }
        )

        return ClassificationBenchmarkExecution(
            probabilities=np.zeros(
                len(X),
                dtype=float,
            ),
            elapsed_seconds=0.125,
        )

    monkeypatch.setattr(
        classification_benchmark,
        "dividir_holdout_temporal",
        fake_split,
    )

    monkeypatch.setattr(
        classification_benchmark,
        "treinar_classificador_triagem",
        forbidden_operational_trainer,
        raising=False,
    )

    monkeypatch.setattr(
        classification_benchmark,
        "_execute_classification_benchmark_model",
        fake_executor,
    )

    result = run_synthetic_classification_benchmark(
        dataset,
    )

    assert executor_calls == [
        {
            "factory_name": "criar_classificador_triagem",
            "n_rows": 200,
            "n_train": 150,
        },
        {
            "factory_name": "criar_classificador_logistic_benchmark",
            "n_rows": 200,
            "n_train": 150,
        },
    ]

    assert result.n_train == 150
    assert result.n_evaluation == 50

    candidate = result.candidates[0]

    assert candidate.model == "decision_tree"
    assert candidate.elapsed_seconds == pytest.approx(0.125)


def test_classification_benchmark_executa_decision_tree_e_logistic_regression_no_mesmo_contrato(
    monkeypatch,
):
    from src.models.classification_benchmark import (
        ClassificationBenchmarkExecution,
    )

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
        dtype=int,
    )

    expected_evaluation = np.arange(
        150,
        200,
        dtype=int,
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

    executor_calls = []

    def fake_executor(
        *,
        model_factory,
        X,
        y,
        train_indices,
    ):
        np.testing.assert_array_equal(
            train_indices,
            expected_train,
        )

        executor_calls.append(
            {
                "factory_name": model_factory.__name__,
                "x_id": id(X),
                "y_id": id(y),
                "n_rows": len(X),
                "n_train": len(train_indices),
            }
        )

        return ClassificationBenchmarkExecution(
            probabilities=np.zeros(
                len(X),
                dtype=float,
            ),
            elapsed_seconds=(0.1 if len(executor_calls) == 1 else 0.2),
        )

    monkeypatch.setattr(
        "src.models.classification_benchmark.dividir_holdout_temporal",
        fake_split,
    )

    monkeypatch.setattr(
        "src.models.classification_benchmark._execute_classification_benchmark_model",
        fake_executor,
    )

    result = run_synthetic_classification_benchmark(
        dataset,
    )

    assert [call["factory_name"] for call in executor_calls] == [
        "criar_classificador_triagem",
        "criar_classificador_logistic_benchmark",
    ]

    assert {call["x_id"] for call in executor_calls}.__len__() == 1

    assert {call["y_id"] for call in executor_calls}.__len__() == 1

    assert all(call["n_rows"] == 200 for call in executor_calls)

    assert all(call["n_train"] == 150 for call in executor_calls)

    assert tuple(candidate.model for candidate in result.candidates) == (
        "decision_tree",
        "logistic_regression",
    )

    assert result.n_train == 150
    assert result.n_evaluation == 50

    assert result.candidates[0].elapsed_seconds == pytest.approx(0.1)

    assert result.candidates[1].elapsed_seconds == pytest.approx(0.2)
