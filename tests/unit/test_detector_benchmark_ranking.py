from src.models.detector_benchmark_ranking import (
    chave_ranking_detector_multi_seed,
    selecionar_campeao_detector_multi_seed,
)
from src.models.detector_benchmark_summary import DetectorBenchmarkSummaryEntry
from src.synthetic.benchmark import MetricSummary


def test_chave_ranking_multi_seed_prioriza_sucesso_sobre_metricas():
    mais_confiavel = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.70,
        win_count=10,
        mean_recall=0.70,
        mean_precision=0.70,
        mean_elapsed_seconds=0.50,
    )

    menos_confiavel = chave_ranking_detector_multi_seed(
        success_count=29,
        mean_f1=0.99,
        win_count=29,
        mean_recall=0.99,
        mean_precision=0.99,
        mean_elapsed_seconds=0.01,
    )

    assert mais_confiavel > menos_confiavel


def test_chave_ranking_multi_seed_prioriza_f1_antes_de_win_count():
    melhor_f1 = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.81,
        win_count=12,
        mean_recall=0.70,
        mean_precision=0.70,
        mean_elapsed_seconds=0.50,
    )

    mais_vitorias = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.80,
        win_count=20,
        mean_recall=0.95,
        mean_precision=0.95,
        mean_elapsed_seconds=0.01,
    )

    assert melhor_f1 > mais_vitorias


def test_chave_ranking_multi_seed_usa_win_count_com_f1_empatado():
    mais_estavel = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.80,
        win_count=18,
        mean_recall=0.70,
        mean_precision=0.70,
        mean_elapsed_seconds=0.50,
    )

    menos_estavel = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.80,
        win_count=12,
        mean_recall=0.99,
        mean_precision=0.99,
        mean_elapsed_seconds=0.01,
    )

    assert mais_estavel > menos_estavel


def test_chave_ranking_multi_seed_preserva_prioridades_metricas_e_tempo():
    melhor_recall = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.80,
        win_count=15,
        mean_recall=0.81,
        mean_precision=0.70,
        mean_elapsed_seconds=0.50,
    )

    melhor_precision = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.80,
        win_count=15,
        mean_recall=0.80,
        mean_precision=0.99,
        mean_elapsed_seconds=0.01,
    )

    assert melhor_recall > melhor_precision

    mais_rapido = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.80,
        win_count=15,
        mean_recall=0.80,
        mean_precision=0.90,
        mean_elapsed_seconds=0.20,
    )

    mais_lento = chave_ranking_detector_multi_seed(
        success_count=30,
        mean_f1=0.80,
        win_count=15,
        mean_recall=0.80,
        mean_precision=0.90,
        mean_elapsed_seconds=0.40,
    )

    assert mais_rapido > mais_lento


def _metric_summary(mean):
    return MetricSummary(
        sample_count=1,
        mean=mean,
        standard_deviation=0.0,
        minimum=mean,
        maximum=mean,
    )


def _detector_summary(
    detector,
    *,
    success_count,
    mean_f1,
    mean_recall,
    mean_precision,
    mean_elapsed_seconds,
):
    run_count = 30

    return DetectorBenchmarkSummaryEntry(
        detector=detector,
        run_count=run_count,
        success_count=success_count,
        error_count=run_count - success_count,
        precision=(
            _metric_summary(mean_precision) if mean_precision is not None else None
        ),
        recall=(_metric_summary(mean_recall) if mean_recall is not None else None),
        f1=(_metric_summary(mean_f1) if mean_f1 is not None else None),
        roc_auc=None,
        alert_rate=None,
        elapsed_seconds=(
            _metric_summary(mean_elapsed_seconds)
            if mean_elapsed_seconds is not None
            else None
        ),
    )


def test_selecionar_campeao_multi_seed_usa_summary_e_win_count():
    summaries = (
        _detector_summary(
            "detector_a",
            success_count=30,
            mean_f1=0.80,
            mean_recall=0.90,
            mean_precision=0.90,
            mean_elapsed_seconds=0.10,
        ),
        _detector_summary(
            "detector_b",
            success_count=30,
            mean_f1=0.80,
            mean_recall=0.70,
            mean_precision=0.70,
            mean_elapsed_seconds=0.50,
        ),
    )

    champion = selecionar_campeao_detector_multi_seed(
        summaries,
        win_counts={
            "detector_a": 10,
            "detector_b": 12,
        },
    )

    assert champion == "detector_b"


def test_selecionar_campeao_multi_seed_trata_win_count_ausente_como_zero():
    summaries = (
        _detector_summary(
            "detector_a",
            success_count=30,
            mean_f1=0.80,
            mean_recall=0.80,
            mean_precision=0.80,
            mean_elapsed_seconds=0.30,
        ),
        _detector_summary(
            "detector_b",
            success_count=30,
            mean_f1=0.80,
            mean_recall=0.80,
            mean_precision=0.80,
            mean_elapsed_seconds=0.30,
        ),
    )

    champion = selecionar_campeao_detector_multi_seed(
        summaries,
        win_counts={
            "detector_a": 1,
        },
    )

    assert champion == "detector_a"


def test_selecionar_campeao_multi_seed_ignora_entry_sem_metricas_validas():
    summaries = (
        _detector_summary(
            "detector_invalido",
            success_count=0,
            mean_f1=None,
            mean_recall=None,
            mean_precision=None,
            mean_elapsed_seconds=None,
        ),
        _detector_summary(
            "detector_valido",
            success_count=29,
            mean_f1=0.70,
            mean_recall=0.70,
            mean_precision=0.70,
            mean_elapsed_seconds=0.40,
        ),
    )

    champion = selecionar_campeao_detector_multi_seed(
        summaries,
        win_counts={
            "detector_invalido": 30,
            "detector_valido": 0,
        },
    )

    assert champion == "detector_valido"


def test_selecionar_campeao_multi_seed_retorna_none_sem_candidatos_validos():
    summaries = (
        _detector_summary(
            "detector_invalido",
            success_count=0,
            mean_f1=None,
            mean_recall=None,
            mean_precision=None,
            mean_elapsed_seconds=None,
        ),
    )

    assert (
        selecionar_campeao_detector_multi_seed(
            summaries,
            win_counts={},
        )
        is None
    )
