from types import SimpleNamespace

from src.models.detector_benchmark_analysis import (
    DetectorBenchmarkMultiSeedAnalysis,
    analisar_detector_benchmark_multi_seed,
)


def test_analisar_detector_benchmark_multi_seed_compoe_resultados(
    monkeypatch,
):
    import src.models.detector_benchmark_analysis as analysis

    detectors_run_1 = (object(), object())
    detectors_run_2 = (object(), object())

    run_1 = SimpleNamespace(
        benchmark=SimpleNamespace(
            detectors=detectors_run_1,
            benchmark_champion="detector_a",
        )
    )
    run_2 = SimpleNamespace(
        benchmark=SimpleNamespace(
            detectors=detectors_run_2,
            benchmark_champion="detector_b",
        )
    )

    harness_result = SimpleNamespace(
        runs=(
            run_1,
            run_2,
        )
    )

    summaries = (object(), object())
    win_counts = {
        "detector_a": 1,
        "detector_b": 1,
    }

    calls = []

    def fake_summarize_detector_benchmark_runs(runs):
        calls.append(
            (
                "summary",
                runs,
            )
        )
        return summaries

    def fake_count_detector_benchmark_wins(runs):
        calls.append(
            (
                "wins",
                runs,
            )
        )
        return win_counts

    def fake_selecionar_campeao_detector_multi_seed(
        received_summaries,
        *,
        win_counts,
    ):
        calls.append(
            (
                "champion",
                received_summaries,
                win_counts,
            )
        )
        return "detector_a"

    monkeypatch.setattr(
        analysis,
        "summarize_detector_benchmark_runs",
        fake_summarize_detector_benchmark_runs,
    )
    monkeypatch.setattr(
        analysis,
        "count_detector_benchmark_wins",
        fake_count_detector_benchmark_wins,
    )
    monkeypatch.setattr(
        analysis,
        "selecionar_campeao_detector_multi_seed",
        fake_selecionar_campeao_detector_multi_seed,
    )

    result = analisar_detector_benchmark_multi_seed(harness_result)

    assert isinstance(
        result,
        DetectorBenchmarkMultiSeedAnalysis,
    )
    assert result.summaries is summaries
    assert result.win_counts is win_counts
    assert result.benchmark_champion == "detector_a"

    assert calls == [
        (
            "summary",
            (
                detectors_run_1,
                detectors_run_2,
            ),
        ),
        (
            "wins",
            harness_result.runs,
        ),
        (
            "champion",
            summaries,
            win_counts,
        ),
    ]


def test_analisar_detector_benchmark_multi_seed_suporta_runs_vazios():
    harness_result = SimpleNamespace(
        runs=(),
    )

    result = analisar_detector_benchmark_multi_seed(harness_result)

    assert result.summaries == ()
    assert result.win_counts == {}
    assert result.benchmark_champion is None
