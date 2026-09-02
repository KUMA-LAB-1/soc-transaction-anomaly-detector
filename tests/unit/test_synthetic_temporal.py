from datetime import datetime, timedelta

import numpy as np
import pytest

from src.synthetic.scenarios import ScenarioDefinition, obter_cenario
from src.synthetic.temporal import TemporalSampler

INICIO = datetime(2026, 1, 1, 0, 0)


def criar_sampler(seed: int = 42) -> TemporalSampler:
    return TemporalSampler(np.random.default_rng(seed))


def test_rejeita_quantidade_maior_que_resolucao_da_janela():
    sampler = criar_sampler()
    fim = INICIO + timedelta(microseconds=2)

    with pytest.raises(ValueError, match="resolução suficiente"):
        sampler.gerar_timestamps(
            obter_cenario("baseline"),
            quantidade=3,
            inicio=INICIO,
            fim=fim,
        )


def test_janela_exclusivamente_diurna_nao_exige_madrugada():
    sampler = criar_sampler()
    inicio = datetime(2026, 1, 1, 12, 0)
    fim = inicio + timedelta(hours=1)

    timestamps = sampler.gerar_timestamps(
        obter_cenario("baseline"),
        quantidade=100,
        inicio=inicio,
        fim=fim,
    )

    assert len(timestamps) == 100
    assert all(6 <= timestamp.hour < 24 for timestamp in timestamps)


def test_janela_exclusivamente_de_madrugada_nao_exige_periodo_diurno():
    sampler = criar_sampler()
    inicio = datetime(2026, 1, 1, 1, 0)
    fim = datetime(2026, 1, 1, 5, 0)

    timestamps = sampler.gerar_timestamps(
        obter_cenario("baseline"),
        quantidade=100,
        inicio=inicio,
        fim=fim,
    )

    assert len(timestamps) == 100
    assert all(timestamp.hour < 6 for timestamp in timestamps)


def test_redistribui_eventos_quando_periodo_diurno_nao_tem_capacidade():
    sampler = criar_sampler()

    cenario = ScenarioDefinition(
        name="redistribuicao-controlada",
        is_suspicious=False,
        valor_mediano=100.0,
        valor_sigma=0.5,
        media_falhas_login=0.0,
        probabilidade_madrugada=0.0,
        probabilidade_dispositivo_novo=0.1,
        probabilidade_alteracao_limite=0.1,
        probabilidade_mudanca_localizacao=0.1,
    )

    inicio = datetime(2026, 1, 1, 5, 59, 59, 999998)
    fim = datetime(2026, 1, 1, 6, 0, 0, 1)

    timestamps = sampler.gerar_timestamps(
        cenario,
        quantidade=3,
        inicio=inicio,
        fim=fim,
    )

    assert len(timestamps) == 3
    assert timestamps == sorted(timestamps)
    assert len(set(timestamps)) == 3
    assert all(inicio <= timestamp < fim for timestamp in timestamps)


@pytest.mark.parametrize(
    "fim",
    [
        INICIO,
        INICIO - timedelta(microseconds=1),
    ],
)
def test_rejeita_janela_temporal_invalida(fim):
    sampler = criar_sampler()

    with pytest.raises(ValueError, match="fim deve ser posterior"):
        sampler.gerar_timestamps(
            obter_cenario("baseline"),
            quantidade=10,
            inicio=INICIO,
            fim=fim,
        )
