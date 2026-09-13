from dataclasses import dataclass

from .classification_benchmark import ClassificationBenchmarkCandidate

_STABILITY_METRICS = (
    "precision",
    "recall",
    "f1",
    "roc_auc",
    "pr_auc",
)


@dataclass(frozen=True, slots=True)
class ClassificationBenchmarkModelStability:
    model: str
    win_count: int
    tie_count: int


@dataclass(frozen=True, slots=True)
class ClassificationBenchmarkMetricStability:
    metric: str
    run_count: int
    evaluated_run_count: int
    unavailable_run_count: int
    models: tuple[ClassificationBenchmarkModelStability, ...]


def _index_run_candidates(
    run: tuple[ClassificationBenchmarkCandidate, ...],
    *,
    run_number: int,
) -> dict[str, ClassificationBenchmarkCandidate]:
    indexed: dict[str, ClassificationBenchmarkCandidate] = {}

    for candidate in run:
        if candidate.model in indexed:
            raise ValueError(
                f"run {run_number} contem candidato duplicado: {candidate.model}"
            )

        indexed[candidate.model] = candidate

    return indexed


def summarize_classification_benchmark_stability(
    runs: tuple[
        tuple[ClassificationBenchmarkCandidate, ...],
        ...,
    ],
) -> tuple[ClassificationBenchmarkMetricStability, ...]:
    if not runs:
        return ()

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

    reference_models = tuple(indexed_runs[0])
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

    summaries: list[ClassificationBenchmarkMetricStability] = []

    for metric in _STABILITY_METRICS:
        win_counts = {model: 0 for model in reference_models}
        tie_counts = {model: 0 for model in reference_models}
        evaluated_run_count = 0
        unavailable_run_count = 0

        for indexed_run in indexed_runs:
            values = {
                model: getattr(
                    indexed_run[model],
                    metric,
                )
                for model in reference_models
            }

            if any(value is None for value in values.values()):
                unavailable_run_count += 1
                continue

            evaluated_run_count += 1

            best_value = max(values.values())

            winners = tuple(
                model for model, value in values.items() if value == best_value
            )

            if len(winners) == 1:
                win_counts[winners[0]] += 1
            else:
                for winner in winners:
                    tie_counts[winner] += 1

        summaries.append(
            ClassificationBenchmarkMetricStability(
                metric=metric,
                run_count=len(runs),
                evaluated_run_count=evaluated_run_count,
                unavailable_run_count=unavailable_run_count,
                models=tuple(
                    ClassificationBenchmarkModelStability(
                        model=model,
                        win_count=win_counts[model],
                        tie_count=tie_counts[model],
                    )
                    for model in reference_models
                ),
            )
        )

    return tuple(summaries)
