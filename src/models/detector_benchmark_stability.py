from .detector_benchmark_harness import DetectorBenchmarkRun


def count_detector_benchmark_wins(
    runs: tuple[DetectorBenchmarkRun, ...],
) -> dict[str, int]:
    wins: dict[str, int] = {}

    for run in runs:
        champion = run.benchmark.benchmark_champion

        if champion is None:
            continue

        wins[champion] = wins.get(champion, 0) + 1

    return wins
