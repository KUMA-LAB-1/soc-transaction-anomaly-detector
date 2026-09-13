from dataclasses import dataclass

from ..synthetic.benchmark import MetricSummary, summarize_metric
from .classification_benchmark import ClassificationBenchmarkCandidate


@dataclass(frozen=True, slots=True)
class ClassificationBenchmarkSummaryEntry:
    model: str
    run_count: int
    precision: MetricSummary | None
    recall: MetricSummary | None
    f1: MetricSummary | None
    roc_auc: MetricSummary | None
    pr_auc: MetricSummary | None
    positive_count: MetricSummary | None
    positive_rate: MetricSummary | None
    false_positives: MetricSummary | None
    false_negatives: MetricSummary | None
    elapsed_seconds: MetricSummary | None


def _index_run_candidates(
    run: tuple[ClassificationBenchmarkCandidate, ...],
    *,
    run_number: int,
) -> dict[str, ClassificationBenchmarkCandidate]:
    indexed: dict[
        str,
        ClassificationBenchmarkCandidate,
    ] = {}

    for entry in run:
        if entry.model in indexed:
            raise ValueError(
                f"run {run_number} contem candidato duplicado: {entry.model}"
            )

        indexed[entry.model] = entry

    return indexed


def summarize_classification_benchmark_runs(
    runs: tuple[
        tuple[ClassificationBenchmarkCandidate, ...],
        ...,
    ],
) -> tuple[ClassificationBenchmarkSummaryEntry, ...]:
    if not runs:
        return ()

    reference_run = runs[0]

    reference_models = tuple(entry.model for entry in reference_run)

    indexed_runs = tuple(
        _index_run_candidates(
            run,
            run_number=run_number,
        )
        for run_number, run in enumerate(
            runs,
            start=1,
        )
    )

    reference_set = set(reference_models)

    for run_number, indexed_run in enumerate(
        indexed_runs[1:],
        start=2,
    ):
        run_models = set(indexed_run)

        missing = reference_set - run_models

        if missing:
            model = sorted(missing)[0]

            raise ValueError(
                f"run {run_number} nao contem candidato presente "
                f"no run de referencia: {model}"
            )

        extra = run_models - reference_set

        if extra:
            model = sorted(extra)[0]

            raise ValueError(
                f"run {run_number} contem candidato ausente "
                f"no run de referencia: {model}"
            )

    summaries: list[ClassificationBenchmarkSummaryEntry] = []

    for model in reference_models:
        entries = tuple(indexed_run[model] for indexed_run in indexed_runs)

        summaries.append(
            ClassificationBenchmarkSummaryEntry(
                model=model,
                run_count=len(entries),
                precision=summarize_metric(tuple(entry.precision for entry in entries)),
                recall=summarize_metric(tuple(entry.recall for entry in entries)),
                f1=summarize_metric(tuple(entry.f1 for entry in entries)),
                roc_auc=summarize_metric(tuple(entry.roc_auc for entry in entries)),
                pr_auc=summarize_metric(tuple(entry.pr_auc for entry in entries)),
                positive_count=summarize_metric(
                    tuple(entry.positive_count for entry in entries)
                ),
                positive_rate=summarize_metric(
                    tuple(entry.positive_rate for entry in entries)
                ),
                false_positives=summarize_metric(
                    tuple(entry.false_positives for entry in entries)
                ),
                false_negatives=summarize_metric(
                    tuple(entry.false_negatives for entry in entries)
                ),
                elapsed_seconds=summarize_metric(
                    tuple(entry.elapsed_seconds for entry in entries)
                ),
            )
        )

    return tuple(summaries)
