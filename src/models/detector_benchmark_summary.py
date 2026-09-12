from dataclasses import dataclass

from ..synthetic.benchmark import MetricSummary, summarize_metric
from .detector_benchmark import DetectorBenchmarkEntry


@dataclass(frozen=True, slots=True)
class DetectorBenchmarkSummaryEntry:
    detector: str
    run_count: int
    success_count: int
    error_count: int
    precision: MetricSummary | None
    recall: MetricSummary | None
    f1: MetricSummary | None
    roc_auc: MetricSummary | None
    alert_rate: MetricSummary | None
    elapsed_seconds: MetricSummary | None


def _index_run_detectors(
    run: tuple[DetectorBenchmarkEntry, ...],
    *,
    run_number: int,
) -> dict[str, DetectorBenchmarkEntry]:
    indexed: dict[str, DetectorBenchmarkEntry] = {}

    for entry in run:
        if entry.detector in indexed:
            raise ValueError(
                f"run {run_number} contem detector duplicado: {entry.detector}"
            )

        indexed[entry.detector] = entry

    return indexed


def summarize_detector_benchmark_runs(
    runs: tuple[
        tuple[DetectorBenchmarkEntry, ...],
        ...,
    ],
) -> tuple[DetectorBenchmarkSummaryEntry, ...]:
    if not runs:
        return ()

    reference_run = runs[0]
    reference_names = tuple(entry.detector for entry in reference_run)

    indexed_runs = tuple(
        _index_run_detectors(
            run,
            run_number=run_number,
        )
        for run_number, run in enumerate(
            runs,
            start=1,
        )
    )

    reference_set = set(reference_names)

    for run_number, indexed_run in enumerate(
        indexed_runs[1:],
        start=2,
    ):
        run_names = set(indexed_run)

        missing = reference_set - run_names

        if missing:
            detector = sorted(missing)[0]

            raise ValueError(
                f"run {run_number} nao contem detector presente "
                f"no run de referencia: {detector}"
            )

        extra = run_names - reference_set

        if extra:
            detector = sorted(extra)[0]

            raise ValueError(
                f"run {run_number} contem detector ausente "
                f"no run de referencia: {detector}"
            )

    summaries: list[DetectorBenchmarkSummaryEntry] = []

    for detector in reference_names:
        entries = tuple(indexed_run[detector] for indexed_run in indexed_runs)

        successful_entries = tuple(entry for entry in entries if entry.status == "ok")

        summaries.append(
            DetectorBenchmarkSummaryEntry(
                detector=detector,
                run_count=len(entries),
                success_count=len(successful_entries),
                error_count=(len(entries) - len(successful_entries)),
                precision=summarize_metric(
                    tuple(entry.precision for entry in successful_entries)
                ),
                recall=summarize_metric(
                    tuple(entry.recall for entry in successful_entries)
                ),
                f1=summarize_metric(tuple(entry.f1 for entry in successful_entries)),
                roc_auc=summarize_metric(
                    tuple(entry.roc_auc for entry in successful_entries)
                ),
                alert_rate=summarize_metric(
                    tuple(entry.alert_rate for entry in successful_entries)
                ),
                elapsed_seconds=summarize_metric(
                    tuple(entry.elapsed_seconds for entry in successful_entries)
                ),
            )
        )

    return tuple(summaries)
