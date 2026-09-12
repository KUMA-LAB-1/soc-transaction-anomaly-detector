from types import SimpleNamespace

from src.models.detector_benchmark_stability import (
    count_detector_benchmark_wins,
)


def test_count_detector_benchmark_wins_conta_campeoes_por_run():
    runs = (
        SimpleNamespace(
            benchmark=SimpleNamespace(
                benchmark_champion="detector_a",
            )
        ),
        SimpleNamespace(
            benchmark=SimpleNamespace(
                benchmark_champion="detector_b",
            )
        ),
        SimpleNamespace(
            benchmark=SimpleNamespace(
                benchmark_champion="detector_a",
            )
        ),
        SimpleNamespace(
            benchmark=SimpleNamespace(
                benchmark_champion=None,
            )
        ),
    )

    result = count_detector_benchmark_wins(runs)

    assert result == {
        "detector_a": 2,
        "detector_b": 1,
    }


def test_count_detector_benchmark_wins_retorna_vazio_sem_campeoes():
    runs = (
        SimpleNamespace(
            benchmark=SimpleNamespace(
                benchmark_champion=None,
            )
        ),
        SimpleNamespace(
            benchmark=SimpleNamespace(
                benchmark_champion=None,
            )
        ),
    )

    assert count_detector_benchmark_wins(runs) == {}
