from .detector_benchmark_summary import DetectorBenchmarkSummaryEntry
from .evaluation import chave_ranking_detector


def chave_ranking_detector_multi_seed(
    *,
    success_count: int,
    mean_f1: float,
    win_count: int,
    mean_recall: float,
    mean_precision: float,
    mean_elapsed_seconds: float,
) -> tuple[int, float, int, float, float, float]:
    metric_ranking = chave_ranking_detector(
        f1=mean_f1,
        recall=mean_recall,
        precision=mean_precision,
        tempo_segundos=mean_elapsed_seconds,
    )

    return (
        success_count,
        metric_ranking[0],
        win_count,
        *metric_ranking[1:],
    )


def selecionar_campeao_detector_multi_seed(
    summaries: tuple[DetectorBenchmarkSummaryEntry, ...],
    *,
    win_counts: dict[str, int],
) -> str | None:
    candidates = tuple(
        summary
        for summary in summaries
        if (
            summary.success_count > 0
            and summary.f1 is not None
            and summary.recall is not None
            and summary.precision is not None
            and summary.elapsed_seconds is not None
        )
    )

    if not candidates:
        return None

    champion = max(
        candidates,
        key=lambda summary: chave_ranking_detector_multi_seed(
            success_count=summary.success_count,
            mean_f1=summary.f1.mean,
            win_count=win_counts.get(
                summary.detector,
                0,
            ),
            mean_recall=summary.recall.mean,
            mean_precision=summary.precision.mean,
            mean_elapsed_seconds=summary.elapsed_seconds.mean,
        ),
    )

    return champion.detector
