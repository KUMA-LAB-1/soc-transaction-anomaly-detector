from dataclasses import dataclass

from .detector_benchmark_harness import DetectorBenchmarkHarnessResult
from .detector_benchmark_ranking import selecionar_campeao_detector_multi_seed
from .detector_benchmark_stability import count_detector_benchmark_wins
from .detector_benchmark_summary import (
    DetectorBenchmarkSummaryEntry,
    summarize_detector_benchmark_runs,
)


@dataclass(frozen=True, slots=True)
class DetectorBenchmarkMultiSeedAnalysis:
    summaries: tuple[DetectorBenchmarkSummaryEntry, ...]
    win_counts: dict[str, int]
    benchmark_champion: str | None


def analisar_detector_benchmark_multi_seed(
    harness_result: DetectorBenchmarkHarnessResult,
) -> DetectorBenchmarkMultiSeedAnalysis:
    detector_runs = tuple(run.benchmark.detectors for run in harness_result.runs)

    summaries = summarize_detector_benchmark_runs(detector_runs)

    win_counts = count_detector_benchmark_wins(harness_result.runs)

    benchmark_champion = selecionar_campeao_detector_multi_seed(
        summaries,
        win_counts=win_counts,
    )

    return DetectorBenchmarkMultiSeedAnalysis(
        summaries=summaries,
        win_counts=win_counts,
        benchmark_champion=benchmark_champion,
    )
