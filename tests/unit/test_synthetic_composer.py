import math
from collections import Counter
from datetime import datetime, timedelta

import pytest

from src.synthetic.composer import MixedDatasetComposer, ScenarioMix
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.scenarios import obter_cenario
from src.synthetic.statistical import StatisticalGenerator

INICIO = datetime(2026, 1, 1, 0, 0)
FIM = INICIO + timedelta(days=7)

POLITICA_SEM_RUIDO = OperationalLabelPolicy(
    probabilidade_falso_positivo=0.0,
    probabilidade_falso_negativo=0.0,
)


@pytest.mark.parametrize(
    "proporcao",
    [
        0.0,
        -0.01,
        1.01,
        math.nan,
        math.inf,
        -math.inf,
        True,
        False,
        "0.50",
        None,
    ],
)
def test_scenario_mix_rejeita_proporcao_invalida(proporcao):
    with pytest.raises(ValueError, match="proporcao"):
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=proporcao,
        )


def test_compositor_respeita_proporcoes_em_total_divisivel():
    gerador = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
    )
    compositor = MixedDatasetComposer(gerador)

    registros = compositor.compor(
        [
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.80,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=0.20,
            ),
        ],
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    contagem = Counter(registro.truth.scenario for registro in registros)

    assert len(registros) == 100
    assert contagem == {
        "baseline": 80,
        "credential_attack": 20,
    }


def test_compositor_distribui_restos_sem_perder_registros():
    gerador = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
    )
    compositor = MixedDatasetComposer(gerador)

    registros = compositor.compor(
        [
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=1 / 3,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=1 / 3,
            ),
            ScenarioMix(
                cenario=obter_cenario("account_takeover"),
                proporcao=1 / 3,
            ),
        ],
        quantidade=10,
        inicio=INICIO,
        fim=FIM,
    )

    contagem = Counter(registro.truth.scenario for registro in registros)

    assert len(registros) == 10
    assert contagem == {
        "baseline": 4,
        "credential_attack": 3,
        "account_takeover": 3,
    }


@pytest.mark.parametrize(
    "proporcoes",
    [
        (0.60, 0.20),
        (0.80, 0.40),
    ],
)
def test_compositor_rejeita_proporcoes_que_nao_somam_um(proporcoes):
    gerador = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
    )
    compositor = MixedDatasetComposer(gerador)

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=proporcoes[0],
        ),
        ScenarioMix(
            cenario=obter_cenario("credential_attack"),
            proporcao=proporcoes[1],
        ),
    ]

    with pytest.raises(ValueError, match="somar 1"):
        compositor.compor(
            misturas,
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
        )


class GeradorQueNaoDeveSerChamado:
    def gerar_registros(self, *args, **kwargs):
        raise AssertionError("o gerador não deveria ser chamado")


@pytest.mark.parametrize(
    "quantidade",
    [
        0,
        -1,
        True,
        1.5,
        "10",
    ],
)
def test_compositor_rejeita_quantidade_invalida_antes_de_chamar_gerador(
    quantidade,
):
    compositor = MixedDatasetComposer(GeradorQueNaoDeveSerChamado())

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=1.0,
        )
    ]

    with pytest.raises(ValueError, match="quantidade"):
        compositor.compor(
            misturas,
            quantidade=quantidade,
            inicio=INICIO,
            fim=FIM,
        )


def test_compositor_rejeita_mistura_vazia():
    gerador = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
    )
    compositor = MixedDatasetComposer(gerador)

    with pytest.raises(ValueError, match="mistura"):
        compositor.compor(
            [],
            quantidade=10,
            inicio=INICIO,
            fim=FIM,
        )


def test_compositor_preserva_ids_unicos_entre_cenarios():
    gerador = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
    )
    compositor = MixedDatasetComposer(gerador)

    registros = compositor.compor(
        [
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.50,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=0.30,
            ),
            ScenarioMix(
                cenario=obter_cenario("account_takeover"),
                proporcao=0.20,
            ),
        ],
        quantidade=100,
        inicio=INICIO,
        fim=FIM,
    )

    ids = [registro.observables["id_transacao"] for registro in registros]

    assert len(ids) == 100
    assert len(set(ids)) == 100
    assert sorted(ids) == list(range(1, 101))


def test_compositor_entrega_dataset_globalmente_cronologico():
    gerador = StatisticalGenerator(
        seed=123,
        label_policy=POLITICA_SEM_RUIDO,
    )
    compositor = MixedDatasetComposer(gerador)

    registros = compositor.compor(
        [
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.50,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=0.30,
            ),
            ScenarioMix(
                cenario=obter_cenario("account_takeover"),
                proporcao=0.20,
            ),
        ],
        quantidade=1000,
        inicio=INICIO,
        fim=FIM,
    )

    timestamps = [registro.observables["data_hora_transacao"] for registro in registros]

    assert timestamps == sorted(timestamps)


def test_compositor_e_reprodutivel_com_mesma_seed_e_configuracao():
    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=0.50,
        ),
        ScenarioMix(
            cenario=obter_cenario("credential_attack"),
            proporcao=0.30,
        ),
        ScenarioMix(
            cenario=obter_cenario("account_takeover"),
            proporcao=0.20,
        ),
    ]

    primeiro_compositor = MixedDatasetComposer(
        StatisticalGenerator(
            seed=2026,
            label_policy=POLITICA_SEM_RUIDO,
        )
    )
    segundo_compositor = MixedDatasetComposer(
        StatisticalGenerator(
            seed=2026,
            label_policy=POLITICA_SEM_RUIDO,
        )
    )

    primeira_execucao = primeiro_compositor.compor(
        misturas,
        quantidade=1000,
        inicio=INICIO,
        fim=FIM,
    )
    segunda_execucao = segundo_compositor.compor(
        misturas,
        quantidade=1000,
        inicio=INICIO,
        fim=FIM,
    )

    assert primeira_execucao == segunda_execucao


def test_compositor_ignora_cenario_com_alocacao_zero():
    gerador = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
    )
    compositor = MixedDatasetComposer(gerador)

    registros = compositor.compor(
        [
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=0.99,
            ),
            ScenarioMix(
                cenario=obter_cenario("credential_attack"),
                proporcao=0.01,
            ),
        ],
        quantidade=1,
        inicio=INICIO,
        fim=FIM,
    )

    assert len(registros) == 1
    assert registros[0].truth.scenario == "baseline"
