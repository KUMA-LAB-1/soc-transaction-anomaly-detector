import pytest

from src.models.classification_benchmark import (
    ClassificationBenchmarkCandidate,
)


def _candidate(
    model,
    *,
    precision,
    recall,
    f1,
    roc_auc,
    pr_auc,
    positive_count,
    positive_rate,
    false_positives,
    false_negatives,
    elapsed_seconds,
):
    return ClassificationBenchmarkCandidate(
        model=model,
        status="ok",
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=roc_auc,
        pr_auc=pr_auc,
        positive_count=positive_count,
        positive_rate=positive_rate,
        false_positives=false_positives,
        false_negatives=false_negatives,
        elapsed_seconds=elapsed_seconds,
    )


def test_summarize_classification_benchmark_runs_agrega_por_modelo():
    from src.models.classification_benchmark_summary import (
        ClassificationBenchmarkSummaryEntry,
        summarize_classification_benchmark_runs,
    )

    run_1 = (
        _candidate(
            "decision_tree",
            precision=0.70,
            recall=0.60,
            f1=0.64,
            roc_auc=0.75,
            pr_auc=0.72,
            positive_count=90,
            positive_rate=0.36,
            false_positives=20,
            false_negatives=40,
            elapsed_seconds=0.010,
        ),
        _candidate(
            "logistic_regression",
            precision=0.74,
            recall=0.70,
            f1=0.72,
            roc_auc=0.82,
            pr_auc=0.80,
            positive_count=100,
            positive_rate=0.40,
            false_positives=24,
            false_negatives=32,
            elapsed_seconds=0.004,
        ),
    )

    # Ordem invertida de propósito.
    run_2 = (
        _candidate(
            "logistic_regression",
            precision=0.78,
            recall=0.74,
            f1=0.76,
            roc_auc=0.86,
            pr_auc=0.84,
            positive_count=110,
            positive_rate=0.44,
            false_positives=22,
            false_negatives=28,
            elapsed_seconds=0.006,
        ),
        _candidate(
            "decision_tree",
            precision=0.80,
            recall=0.70,
            f1=0.76,
            roc_auc=0.81,
            pr_auc=0.78,
            positive_count=100,
            positive_rate=0.40,
            false_positives=18,
            false_negatives=30,
            elapsed_seconds=0.014,
        ),
    )

    summary = summarize_classification_benchmark_runs(
        (
            run_1,
            run_2,
        )
    )

    assert tuple(entry.model for entry in summary) == (
        "decision_tree",
        "logistic_regression",
    )

    assert all(
        isinstance(
            entry,
            ClassificationBenchmarkSummaryEntry,
        )
        for entry in summary
    )

    decision_tree = summary[0]

    assert decision_tree.run_count == 2

    assert decision_tree.f1.sample_count == 2
    assert decision_tree.f1.mean == pytest.approx(0.70)
    assert decision_tree.f1.standard_deviation == pytest.approx(0.06)
    assert decision_tree.f1.minimum == pytest.approx(0.64)
    assert decision_tree.f1.maximum == pytest.approx(0.76)

    assert decision_tree.roc_auc.mean == pytest.approx(0.78)
    assert decision_tree.pr_auc.mean == pytest.approx(0.75)

    assert decision_tree.false_positives.mean == pytest.approx(19.0)
    assert decision_tree.false_negatives.mean == pytest.approx(35.0)

    assert decision_tree.elapsed_seconds.mean == pytest.approx(0.012)

    logistic = summary[1]

    assert logistic.run_count == 2
    assert logistic.f1.mean == pytest.approx(0.74)
    assert logistic.roc_auc.mean == pytest.approx(0.84)
    assert logistic.pr_auc.mean == pytest.approx(0.82)


def test_summarize_classification_benchmark_runs_rejeita_candidato_duplicado():
    from src.models.classification_benchmark_summary import (
        summarize_classification_benchmark_runs,
    )

    duplicated_run = (
        _candidate(
            "decision_tree",
            precision=0.70,
            recall=0.60,
            f1=0.64,
            roc_auc=0.75,
            pr_auc=0.72,
            positive_count=90,
            positive_rate=0.36,
            false_positives=20,
            false_negatives=40,
            elapsed_seconds=0.010,
        ),
        _candidate(
            "decision_tree",
            precision=0.80,
            recall=0.70,
            f1=0.76,
            roc_auc=0.81,
            pr_auc=0.78,
            positive_count=100,
            positive_rate=0.40,
            false_positives=18,
            false_negatives=30,
            elapsed_seconds=0.014,
        ),
    )

    with pytest.raises(
        ValueError,
        match="run 1 contem candidato duplicado: decision_tree",
    ):
        summarize_classification_benchmark_runs((duplicated_run,))


def test_summarize_classification_benchmark_runs_rejeita_candidato_ausente():
    from src.models.classification_benchmark_summary import (
        summarize_classification_benchmark_runs,
    )

    decision_tree = _candidate(
        "decision_tree",
        precision=0.70,
        recall=0.60,
        f1=0.64,
        roc_auc=0.75,
        pr_auc=0.72,
        positive_count=90,
        positive_rate=0.36,
        false_positives=20,
        false_negatives=40,
        elapsed_seconds=0.010,
    )

    logistic_regression = _candidate(
        "logistic_regression",
        precision=0.74,
        recall=0.70,
        f1=0.72,
        roc_auc=0.82,
        pr_auc=0.80,
        positive_count=100,
        positive_rate=0.40,
        false_positives=24,
        false_negatives=32,
        elapsed_seconds=0.004,
    )

    reference_run = (
        decision_tree,
        logistic_regression,
    )

    incomplete_run = (decision_tree,)

    with pytest.raises(
        ValueError,
        match=(
            "run 2 nao contem candidato presente "
            "no run de referencia: logistic_regression"
        ),
    ):
        summarize_classification_benchmark_runs(
            (
                reference_run,
                incomplete_run,
            )
        )


def test_summarize_classification_benchmark_runs_rejeita_candidato_extra():
    from src.models.classification_benchmark_summary import (
        summarize_classification_benchmark_runs,
    )

    decision_tree = _candidate(
        "decision_tree",
        precision=0.70,
        recall=0.60,
        f1=0.64,
        roc_auc=0.75,
        pr_auc=0.72,
        positive_count=90,
        positive_rate=0.36,
        false_positives=20,
        false_negatives=40,
        elapsed_seconds=0.010,
    )

    logistic_regression = _candidate(
        "logistic_regression",
        precision=0.74,
        recall=0.70,
        f1=0.72,
        roc_auc=0.82,
        pr_auc=0.80,
        positive_count=100,
        positive_rate=0.40,
        false_positives=24,
        false_negatives=32,
        elapsed_seconds=0.004,
    )

    random_forest = _candidate(
        "random_forest",
        precision=0.78,
        recall=0.72,
        f1=0.75,
        roc_auc=0.85,
        pr_auc=0.83,
        positive_count=105,
        positive_rate=0.42,
        false_positives=21,
        false_negatives=30,
        elapsed_seconds=0.020,
    )

    reference_run = (
        decision_tree,
        logistic_regression,
    )

    expanded_run = (
        decision_tree,
        logistic_regression,
        random_forest,
    )

    with pytest.raises(
        ValueError,
        match=("run 2 contem candidato ausente no run de referencia: random_forest"),
    ):
        summarize_classification_benchmark_runs(
            (
                reference_run,
                expanded_run,
            )
        )


def test_summarize_classification_benchmark_runs_retorna_vazio_sem_runs():
    from src.models.classification_benchmark_summary import (
        summarize_classification_benchmark_runs,
    )

    assert summarize_classification_benchmark_runs(()) == ()
