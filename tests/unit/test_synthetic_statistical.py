from datetime import datetime, timedelta

import pytest

from src.synthetic.contracts import SyntheticRecord
from src.synthetic.firewall import projetar_dataset_modelagem
from src.synthetic.scenarios import obter_cenario
from src.synthetic.statistical import StatisticalGenerator

INICIO = datetime(2026, 1, 1, 0, 0)
FIM_PADRAO = INICIO + timedelta(days=30)

SINAIS_BOOLEANOS = (
    "dispositivo_novo_flag",
    "alteracao_limite_flag",
    "mudanca_localizacao_flag",
)


def gerar(
    nome_cenario: str,
    *,
    seed: int = 42,
    quantidade: int = 100,
) -> list[SyntheticRecord]:
    gerador = StatisticalGenerator(seed=seed)

    return gerador.gerar_registros(
        obter_cenario(nome_cenario),
        quantidade=quantidade,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )


def test_mesma_seed_reproduz_exatamente_os_mesmos_registros():
    primeira_execucao = gerar(
        "baseline",
        seed=42,
        quantidade=100,
    )
    segunda_execucao = gerar(
        "baseline",
        seed=42,
        quantidade=100,
    )

    assert primeira_execucao == segunda_execucao


def test_seeds_diferentes_produzem_registros_diferentes():
    primeira_execucao = gerar(
        "baseline",
        seed=42,
        quantidade=100,
    )
    segunda_execucao = gerar(
        "baseline",
        seed=43,
        quantidade=100,
    )

    assert primeira_execucao != segunda_execucao


def test_gerador_retorna_synthetic_records():
    registros = gerar(
        "baseline",
        quantidade=10,
    )

    assert len(registros) == 10
    assert all(isinstance(registro, SyntheticRecord) for registro in registros)


def test_registro_contem_observaveis_minimos_do_pipeline():
    registro = gerar(
        "baseline",
        quantidade=1,
    )[0]

    campos_esperados = {
        "id_transacao",
        "cliente_pseudonimo",
        "data_hora_transacao",
        "tipo_transacao",
        "valor_transacao",
        "falhas_login_recentes",
        "dispositivo_novo_flag",
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    }

    assert campos_esperados <= set(registro.observables)
    assert set(registro.operational_labels) == {"status_transacao"}


@pytest.mark.parametrize(
    "nome_cenario",
    [
        "baseline",
        "credential_attack",
        "account_takeover",
        "location_anomaly",
        "transaction_anomaly",
    ],
)
def test_ground_truth_reflete_o_cenario_gerador(nome_cenario):
    cenario = obter_cenario(nome_cenario)

    registro = gerar(
        nome_cenario,
        quantidade=1,
    )[0]

    assert registro.truth.scenario == cenario.name
    assert registro.truth.is_suspicious is cenario.is_suspicious
    assert registro.truth.expected_mitre_techniques == cenario.expected_mitre_techniques


def test_ground_truth_nao_vaza_para_dataset_de_modelagem():
    registros = gerar(
        "credential_attack",
        quantidade=100,
    )

    dataset = projetar_dataset_modelagem(registros)

    assert "scenario" not in dataset.columns
    assert "is_suspicious" not in dataset.columns
    assert "attack_profile" not in dataset.columns
    assert "expected_mitre_techniques" not in dataset.columns


@pytest.mark.parametrize(
    "nome_cenario",
    [
        "baseline",
        "account_takeover",
    ],
)
def test_sinais_booleanos_nao_sao_deterministicos(nome_cenario):
    registros = gerar(
        nome_cenario,
        quantidade=2000,
    )

    for campo in SINAIS_BOOLEANOS:
        valores = [bool(registro.observables[campo]) for registro in registros]

        assert any(valores)
        assert not all(valores)


@pytest.mark.parametrize(
    "nome_cenario",
    [
        "baseline",
        "account_takeover",
    ],
)
def test_horario_possui_sobreposicao_entre_dia_e_madrugada(nome_cenario):
    registros = gerar(
        nome_cenario,
        quantidade=2000,
    )

    horas = [registro.observables["data_hora_transacao"].hour for registro in registros]

    assert any(hora < 6 for hora in horas)
    assert any(hora >= 6 for hora in horas)


def test_account_takeover_tem_maior_frequencia_de_dispositivo_novo_que_baseline():
    baseline = gerar(
        "baseline",
        seed=123,
        quantidade=3000,
    )
    account_takeover = gerar(
        "account_takeover",
        seed=123,
        quantidade=3000,
    )

    taxa_baseline = sum(
        bool(registro.observables["dispositivo_novo_flag"]) for registro in baseline
    ) / len(baseline)

    taxa_account_takeover = sum(
        bool(registro.observables["dispositivo_novo_flag"])
        for registro in account_takeover
    ) / len(account_takeover)

    assert taxa_baseline < taxa_account_takeover


def test_valores_sao_positivos_e_falhas_login_nao_negativas():
    registros = gerar(
        "transaction_anomaly",
        quantidade=500,
    )

    for registro in registros:
        assert registro.observables["valor_transacao"] > 0

        falhas = registro.observables["falhas_login_recentes"]

        assert isinstance(falhas, int)
        assert falhas >= 0


def test_timestamps_sao_cronologicos_e_unicos():
    registros = gerar(
        "baseline",
        quantidade=100,
    )

    timestamps = [registro.observables["data_hora_transacao"] for registro in registros]

    assert timestamps == sorted(timestamps)
    assert len(timestamps) == len(set(timestamps))


@pytest.mark.parametrize(
    "quantidade",
    [
        0,
        -1,
    ],
)
def test_gerador_rejeita_quantidade_nao_positiva(quantidade):
    gerador = StatisticalGenerator(seed=42)

    with pytest.raises(ValueError, match="quantidade"):
        gerador.gerar_registros(
            obter_cenario("baseline"),
            quantidade=quantidade,
            inicio=INICIO,
            fim=FIM_PADRAO,
        )


def test_multiplos_lotes_no_mesmo_gerador_nao_reutilizam_ids():
    gerador = StatisticalGenerator(seed=42)

    primeiro_lote = gerador.gerar_registros(
        obter_cenario("baseline"),
        quantidade=3,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )
    segundo_lote = gerador.gerar_registros(
        obter_cenario("account_takeover"),
        quantidade=3,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    ids_primeiro_lote = [
        registro.observables["id_transacao"] for registro in primeiro_lote
    ]
    ids_segundo_lote = [
        registro.observables["id_transacao"] for registro in segundo_lote
    ]

    assert ids_primeiro_lote == [1, 2, 3]
    assert ids_segundo_lote == [4, 5, 6]
    assert set(ids_primeiro_lote).isdisjoint(ids_segundo_lote)


@pytest.mark.parametrize(
    "quantidade",
    [
        True,
        1.5,
        "10",
    ],
)
def test_gerador_rejeita_quantidade_que_nao_e_inteiro(quantidade):
    gerador = StatisticalGenerator(seed=42)

    with pytest.raises(ValueError, match="inteiro positivo"):
        gerador.gerar_registros(
            obter_cenario("baseline"),
            quantidade=quantidade,
            inicio=INICIO,
            fim=FIM_PADRAO,
        )


def test_gerador_respeita_janela_temporal_densa():
    gerador = StatisticalGenerator(seed=42)
    fim = INICIO + timedelta(days=1)

    registros = gerador.gerar_registros(
        obter_cenario("baseline"),
        quantidade=10_000,
        inicio=INICIO,
        fim=fim,
    )

    timestamps = [registro.observables["data_hora_transacao"] for registro in registros]

    assert len(timestamps) == 10_000
    assert timestamps == sorted(timestamps)
    assert len(timestamps) == len(set(timestamps))
    assert all(INICIO <= timestamp < fim for timestamp in timestamps)


@pytest.mark.parametrize(
    "fim",
    [
        INICIO,
        INICIO - timedelta(microseconds=1),
    ],
)
def test_gerador_rejeita_janela_temporal_invalida(fim):
    gerador = StatisticalGenerator(seed=42)

    with pytest.raises(ValueError, match="fim deve ser posterior"):
        gerador.gerar_registros(
            obter_cenario("baseline"),
            quantidade=10,
            inicio=INICIO,
            fim=fim,
        )


def test_mesma_seed_reproduz_exatamente_a_mesma_janela_temporal():
    fim = INICIO + timedelta(days=2)

    primeira_execucao = StatisticalGenerator(seed=777).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=1000,
        inicio=INICIO,
        fim=fim,
    )
    segunda_execucao = StatisticalGenerator(seed=777).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=1000,
        inicio=INICIO,
        fim=fim,
    )

    assert primeira_execucao == segunda_execucao


def test_janela_temporal_preserva_diferenca_de_probabilidade_de_madrugada():
    fim = INICIO + timedelta(days=7)

    baseline = StatisticalGenerator(seed=321).gerar_registros(
        obter_cenario("baseline"),
        quantidade=5000,
        inicio=INICIO,
        fim=fim,
    )
    credential_attack = StatisticalGenerator(seed=321).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=5000,
        inicio=INICIO,
        fim=fim,
    )

    taxa_baseline = sum(
        registro.observables["data_hora_transacao"].hour < 6 for registro in baseline
    ) / len(baseline)

    taxa_credential_attack = sum(
        registro.observables["data_hora_transacao"].hour < 6
        for registro in credential_attack
    ) / len(credential_attack)

    assert 0 < taxa_baseline < 1
    assert 0 < taxa_credential_attack < 1
    assert taxa_baseline < taxa_credential_attack
