import pytest

from src.models.detector_benchmark import DetectorBenchmarkEntry
from src.models.detector_benchmark_summary import (
    summarize_detector_benchmark_runs,
)


def _ok_entry(
    detector,
    *,
    precision,
    recall,
    f1,
    roc_auc,
    alert_rate,
    elapsed_seconds,
):
    return DetectorBenchmarkEntry(
        detector=detector,
        status="ok",
        precision=precision,
        recall=recall,
        f1=f1,
        roc_auc=roc_auc,
        false_positives=1,
        false_negatives=2,
        alert_count=10,
        alert_rate=alert_rate,
        elapsed_seconds=elapsed_seconds,
    )


def _error_entry(
    detector,
    *,
    elapsed_seconds,
):
    return DetectorBenchmarkEntry(
        detector=detector,
        status="erro",
        precision=None,
        recall=None,
        f1=None,
        roc_auc=None,
        false_positives=None,
        false_negatives=None,
        alert_count=None,
        alert_rate=None,
        elapsed_seconds=elapsed_seconds,
        error="falha simulada",
    )


def test_summarize_detector_benchmark_runs_agrega_por_nome_e_ignora_erros():
    run_1 = (
        _ok_entry(
            "detector_a",
            precision=0.80,
            recall=0.70,
            f1=0.75,
            roc_auc=0.81,
            alert_rate=0.20,
            elapsed_seconds=0.40,
        ),
        _error_entry(
            "detector_b",
            elapsed_seconds=0.01,
        ),
    )

    run_2 = (
        _ok_entry(
            "detector_b",
            precision=0.60,
            recall=0.90,
            f1=0.72,
            roc_auc=0.76,
            alert_rate=0.30,
            elapsed_seconds=0.30,
        ),
        _ok_entry(
            "detector_a",
            precision=0.90,
            recall=0.80,
            f1=0.85,
            roc_auc=0.88,
            alert_rate=0.25,
            elapsed_seconds=0.20,
        ),
    )

    summary = summarize_detector_benchmark_runs(
        (
            run_1,
            run_2,
        )
    )

    assert tuple(entry.detector for entry in summary) == (
        "detector_a",
        "detector_b",
    )

    detector_a = summary[0]

    assert detector_a.run_count == 2
    assert detector_a.success_count == 2
    assert detector_a.error_count == 0

    assert detector_a.f1 is not None
    assert detector_a.f1.sample_count == 2
    assert detector_a.f1.mean == pytest.approx(0.80)
    assert detector_a.f1.standard_deviation == pytest.approx(0.05)
    assert detector_a.f1.minimum == pytest.approx(0.75)
    assert detector_a.f1.maximum == pytest.approx(0.85)

    assert detector_a.elapsed_seconds is not None
    assert detector_a.elapsed_seconds.mean == pytest.approx(0.30)

    detector_b = summary[1]

    assert detector_b.run_count == 2
    assert detector_b.success_count == 1
    assert detector_b.error_count == 1

    assert detector_b.f1 is not None
    assert detector_b.f1.sample_count == 1
    assert detector_b.f1.mean == pytest.approx(0.72)

    assert detector_b.elapsed_seconds is not None
    assert detector_b.elapsed_seconds.sample_count == 1
    assert detector_b.elapsed_seconds.mean == pytest.approx(0.30)


def test_summarize_detector_benchmark_runs_rejeita_detector_ausente():
    run_1 = (
        _ok_entry(
            "detector_a",
            precision=0.80,
            recall=0.70,
            f1=0.75,
            roc_auc=0.81,
            alert_rate=0.20,
            elapsed_seconds=0.40,
        ),
        _ok_entry(
            "detector_b",
            precision=0.60,
            recall=0.90,
            f1=0.72,
            roc_auc=0.76,
            alert_rate=0.30,
            elapsed_seconds=0.30,
        ),
    )

    run_2 = (
        _ok_entry(
            "detector_a",
            precision=0.90,
            recall=0.80,
            f1=0.85,
            roc_auc=0.88,
            alert_rate=0.25,
            elapsed_seconds=0.20,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("run 2 nao contem detector presente no run de referencia: detector_b"),
    ):
        summarize_detector_benchmark_runs(
            (
                run_1,
                run_2,
            )
        )


def test_summarize_detector_benchmark_runs_rejeita_detector_extra():
    run_1 = (
        _ok_entry(
            "detector_a",
            precision=0.80,
            recall=0.70,
            f1=0.75,
            roc_auc=0.81,
            alert_rate=0.20,
            elapsed_seconds=0.40,
        ),
    )

    run_2 = (
        _ok_entry(
            "detector_a",
            precision=0.90,
            recall=0.80,
            f1=0.85,
            roc_auc=0.88,
            alert_rate=0.25,
            elapsed_seconds=0.20,
        ),
        _ok_entry(
            "detector_b",
            precision=0.60,
            recall=0.90,
            f1=0.72,
            roc_auc=0.76,
            alert_rate=0.30,
            elapsed_seconds=0.30,
        ),
    )

    with pytest.raises(
        ValueError,
        match=("run 2 contem detector ausente no run de referencia: detector_b"),
    ):
        summarize_detector_benchmark_runs(
            (
                run_1,
                run_2,
            )
        )


def test_summarize_detector_benchmark_runs_rejeita_detector_duplicado():
    run_1 = (
        _ok_entry(
            "detector_a",
            precision=0.80,
            recall=0.70,
            f1=0.75,
            roc_auc=0.81,
            alert_rate=0.20,
            elapsed_seconds=0.40,
        ),
        _ok_entry(
            "detector_a",
            precision=0.90,
            recall=0.80,
            f1=0.85,
            roc_auc=0.88,
            alert_rate=0.25,
            elapsed_seconds=0.20,
        ),
    )

    with pytest.raises(
        ValueError,
        match="run 1 contem detector duplicado: detector_a",
    ):
        summarize_detector_benchmark_runs((run_1,))


def test_summarize_detector_benchmark_runs_retorna_vazio_sem_runs():
    assert summarize_detector_benchmark_runs(()) == ()
