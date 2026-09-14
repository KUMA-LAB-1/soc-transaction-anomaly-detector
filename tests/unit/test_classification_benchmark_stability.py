import pytest

from src.models.classification_benchmark import (
    ClassificationBenchmarkCandidate,
)
from src.models.classification_benchmark_stability import (
    ClassificationBenchmarkMetricStability,
    ClassificationBenchmarkModelStability,
    summarize_classification_benchmark_stability,
)


def _candidate(
    model: str,
    *,
    precision: float,
    recall: float,
    f1: float,
    roc_auc: float | None,
    pr_auc: float | None,
) -> ClassificationBenchmarkCandidate:
    return ClassificationBenchmarkCandidate(
        model=model,
        status="ok",
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=roc_auc,
        pr_auc=pr_auc,
        positive_count=10,
        positive_rate=0.10,
        false_positives=2,
        false_negatives=3,
        elapsed_seconds=0.01,
    )


def test_summarize_classification_benchmark_stability_conta_vitorias_por_metrica():
    runs = (
        (
            _candidate(
                "decision_tree",
                precision=0.70,
                recall=0.60,
                f1=0.64,
                roc_auc=0.75,
                pr_auc=0.72,
            ),
            _candidate(
                "logistic_regression",
                precision=0.72,
                recall=0.70,
                f1=0.71,
                roc_auc=0.82,
                pr_auc=0.80,
            ),
            _candidate(
                "random_forest",
                precision=0.80,
                recall=0.76,
                f1=0.78,
                roc_auc=0.87,
                pr_auc=0.85,
            ),
        ),
        (
            # Ordem invertida de propósito.
            _candidate(
                "logistic_regression",
                precision=0.73,
                recall=0.68,
                f1=0.70,
                roc_auc=0.83,
                pr_auc=0.81,
            ),
            _candidate(
                "decision_tree",
                precision=0.78,
                recall=0.76,
                f1=0.77,
                roc_auc=0.79,
                pr_auc=0.76,
            ),
            _candidate(
                "random_forest",
                precision=0.75,
                recall=0.74,
                f1=0.75,
                roc_auc=0.78,
                pr_auc=0.77,
            ),
        ),
    )

    result = summarize_classification_benchmark_stability(runs)

    assert tuple(entry.metric for entry in result) == (
        "precision",
        "recall",
        "f1",
        "roc_auc",
        "pr_auc",
    )

    f1_stability = next(entry for entry in result if entry.metric == "f1")

    assert isinstance(
        f1_stability,
        ClassificationBenchmarkMetricStability,
    )
    assert f1_stability.run_count == 2
    assert f1_stability.evaluated_run_count == 2
    assert f1_stability.unavailable_run_count == 0

    assert f1_stability.models == (
        ClassificationBenchmarkModelStability(
            model="decision_tree",
            win_count=1,
            tie_count=0,
        ),
        ClassificationBenchmarkModelStability(
            model="logistic_regression",
            win_count=0,
            tie_count=0,
        ),
        ClassificationBenchmarkModelStability(
            model="random_forest",
            win_count=1,
            tie_count=0,
        ),
    )


def test_summarize_classification_benchmark_stability_conta_empate_sem_vitoria():
    runs = (
        (
            _candidate(
                "decision_tree",
                precision=0.70,
                recall=0.60,
                f1=0.70,
                roc_auc=0.75,
                pr_auc=0.72,
            ),
            _candidate(
                "logistic_regression",
                precision=0.72,
                recall=0.68,
                f1=0.70,
                roc_auc=0.82,
                pr_auc=0.80,
            ),
        ),
    )

    result = summarize_classification_benchmark_stability(runs)

    f1_stability = next(entry for entry in result if entry.metric == "f1")

    assert f1_stability.run_count == 1
    assert f1_stability.evaluated_run_count == 1
    assert f1_stability.unavailable_run_count == 0

    assert f1_stability.models == (
        ClassificationBenchmarkModelStability(
            model="decision_tree",
            win_count=0,
            tie_count=1,
        ),
        ClassificationBenchmarkModelStability(
            model="logistic_regression",
            win_count=0,
            tie_count=1,
        ),
    )


def test_summarize_classification_benchmark_stability_ignora_run_com_metrica_indisponivel():
    runs = (
        (
            _candidate(
                "decision_tree",
                precision=0.70,
                recall=0.60,
                f1=0.64,
                roc_auc=0.75,
                pr_auc=0.72,
            ),
            _candidate(
                "logistic_regression",
                precision=0.72,
                recall=0.70,
                f1=0.71,
                roc_auc=0.82,
                pr_auc=0.80,
            ),
        ),
        (
            _candidate(
                "decision_tree",
                precision=0.78,
                recall=0.76,
                f1=0.77,
                roc_auc=0.79,
                pr_auc=0.76,
            ),
            _candidate(
                "logistic_regression",
                precision=0.73,
                recall=0.68,
                f1=0.70,
                roc_auc=None,
                pr_auc=0.81,
            ),
        ),
    )

    result = summarize_classification_benchmark_stability(runs)

    roc_auc_stability = next(entry for entry in result if entry.metric == "roc_auc")

    assert roc_auc_stability.run_count == 2
    assert roc_auc_stability.evaluated_run_count == 1
    assert roc_auc_stability.unavailable_run_count == 1

    assert roc_auc_stability.models == (
        ClassificationBenchmarkModelStability(
            model="decision_tree",
            win_count=0,
            tie_count=0,
        ),
        ClassificationBenchmarkModelStability(
            model="logistic_regression",
            win_count=1,
            tie_count=0,
        ),
    )


def test_summarize_classification_benchmark_stability_rejeita_candidato_duplicado():
    runs = (
        (
            _candidate(
                "decision_tree",
                precision=0.70,
                recall=0.60,
                f1=0.64,
                roc_auc=0.75,
                pr_auc=0.72,
            ),
            _candidate(
                "decision_tree",
                precision=0.71,
                recall=0.61,
                f1=0.65,
                roc_auc=0.76,
                pr_auc=0.73,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match="run 1 contem candidato duplicado: decision_tree",
    ):
        summarize_classification_benchmark_stability(runs)


def test_summarize_classification_benchmark_stability_rejeita_candidato_ausente():
    runs = (
        (
            _candidate(
                "decision_tree",
                precision=0.70,
                recall=0.60,
                f1=0.64,
                roc_auc=0.75,
                pr_auc=0.72,
            ),
            _candidate(
                "logistic_regression",
                precision=0.72,
                recall=0.70,
                f1=0.71,
                roc_auc=0.82,
                pr_auc=0.80,
            ),
        ),
        (
            _candidate(
                "decision_tree",
                precision=0.78,
                recall=0.76,
                f1=0.77,
                roc_auc=0.79,
                pr_auc=0.76,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=(
            "run 2 nao contem candidato presente "
            "no run de referencia: logistic_regression"
        ),
    ):
        summarize_classification_benchmark_stability(runs)


def test_summarize_classification_benchmark_stability_rejeita_candidato_extra():
    runs = (
        (
            _candidate(
                "decision_tree",
                precision=0.70,
                recall=0.60,
                f1=0.64,
                roc_auc=0.75,
                pr_auc=0.72,
            ),
            _candidate(
                "logistic_regression",
                precision=0.72,
                recall=0.70,
                f1=0.71,
                roc_auc=0.82,
                pr_auc=0.80,
            ),
        ),
        (
            _candidate(
                "decision_tree",
                precision=0.78,
                recall=0.76,
                f1=0.77,
                roc_auc=0.79,
                pr_auc=0.76,
            ),
            _candidate(
                "logistic_regression",
                precision=0.73,
                recall=0.68,
                f1=0.70,
                roc_auc=0.83,
                pr_auc=0.81,
            ),
            _candidate(
                "random_forest",
                precision=0.80,
                recall=0.74,
                f1=0.77,
                roc_auc=0.85,
                pr_auc=0.84,
            ),
        ),
    )

    with pytest.raises(
        ValueError,
        match=("run 2 contem candidato ausente no run de referencia: random_forest"),
    ):
        summarize_classification_benchmark_stability(runs)


def test_summarize_classification_benchmark_stability_retorna_vazio_sem_runs():
    assert summarize_classification_benchmark_stability(()) == ()
