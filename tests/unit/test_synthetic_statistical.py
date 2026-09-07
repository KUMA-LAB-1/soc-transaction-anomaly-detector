from datetime import datetime, timedelta

import pytest

from src.synthetic.contracts import SyntheticRecord
from src.synthetic.firewall import projetar_dataset_modelagem
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.population import (
    CustomerBehaviorProfile,
    CustomerPopulation,
)
from src.synthetic.scenarios import obter_cenario
from src.synthetic.statistical import StatisticalGenerator

INICIO = datetime(2026, 1, 1, 0, 0)
FIM_PADRAO = INICIO + timedelta(days=30)

POLITICA_SEM_RUIDO = OperationalLabelPolicy(
    probabilidade_falso_positivo=0.0,
    probabilidade_falso_negativo=0.0,
)

SINAIS_BOOLEANOS = (
    "dispositivo_novo_flag",
    "alteracao_limite_flag",
    "mudanca_localizacao_flag",
)


def criar_populacao(
    customer_pseudonym: str,
    *,
    transaction_value_median: float = 180.0,
    transaction_value_sigma: float = 0.65,
    recent_login_failure_rate: float = 0.15,
) -> CustomerPopulation:
    return CustomerPopulation(
        profiles=(
            CustomerBehaviorProfile(
                customer_pseudonym=customer_pseudonym,
                transaction_value_median=transaction_value_median,
                transaction_value_sigma=transaction_value_sigma,
                recent_login_failure_rate=recent_login_failure_rate,
            ),
        )
    )


def test_gerador_com_populacao_usa_pseudonimo_do_profile():
    population = criar_populacao(
        "entidade-sintetica-alpha",
    )

    gerador = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population,
    )

    registros = gerador.gerar_registros(
        obter_cenario("baseline"),
        quantidade=20,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    assert {registro.observables["cliente_pseudonimo"] for registro in registros} == {
        "entidade-sintetica-alpha",
    }


def test_gerador_rejeita_population_invalida():
    with pytest.raises(
        ValueError,
        match="population",
    ):
        StatisticalGenerator(
            seed=42,
            label_policy=POLITICA_SEM_RUIDO,
            population="population-invalida",
        )


def test_mudar_apenas_identidade_da_populacao_nao_altera_evento():
    population_alpha = criar_populacao(
        "entidade-alpha",
    )
    population_beta = criar_populacao(
        "entidade-beta",
    )

    registros_alpha = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_alpha,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_beta = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_beta,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    observaveis_alpha = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "cliente_pseudonimo"
        }
        for registro in registros_alpha
    ]

    observaveis_beta = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "cliente_pseudonimo"
        }
        for registro in registros_beta
    ]

    assert observaveis_alpha == observaveis_beta

    assert [registro.operational_labels for registro in registros_alpha] == [
        registro.operational_labels for registro in registros_beta
    ]

    assert [registro.truth for registro in registros_alpha] == [
        registro.truth for registro in registros_beta
    ]


def criar_gerador(seed: int) -> StatisticalGenerator:
    return StatisticalGenerator(
        seed=seed,
        label_policy=POLITICA_SEM_RUIDO,
    )


def gerar(
    nome_cenario: str,
    *,
    seed: int = 42,
    quantidade: int = 100,
) -> list[SyntheticRecord]:
    gerador = criar_gerador(seed)

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
    gerador = criar_gerador(seed=42)

    with pytest.raises(ValueError, match="quantidade"):
        gerador.gerar_registros(
            obter_cenario("baseline"),
            quantidade=quantidade,
            inicio=INICIO,
            fim=FIM_PADRAO,
        )


def test_multiplos_lotes_no_mesmo_gerador_nao_reutilizam_ids():
    gerador = criar_gerador(seed=42)

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
    gerador = criar_gerador(seed=42)

    with pytest.raises(ValueError, match="inteiro positivo"):
        gerador.gerar_registros(
            obter_cenario("baseline"),
            quantidade=quantidade,
            inicio=INICIO,
            fim=FIM_PADRAO,
        )


def test_gerador_respeita_janela_temporal_densa():
    gerador = criar_gerador(seed=42)
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
    gerador = criar_gerador(seed=42)

    with pytest.raises(ValueError, match="fim deve ser posterior"):
        gerador.gerar_registros(
            obter_cenario("baseline"),
            quantidade=10,
            inicio=INICIO,
            fim=fim,
        )


def test_mesma_seed_reproduz_exatamente_a_mesma_janela_temporal():
    fim = INICIO + timedelta(days=2)

    primeira_execucao = criar_gerador(seed=777).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=1000,
        inicio=INICIO,
        fim=fim,
    )
    segunda_execucao = criar_gerador(seed=777).gerar_registros(
        obter_cenario("credential_attack"),
        quantidade=1000,
        inicio=INICIO,
        fim=fim,
    )

    assert primeira_execucao == segunda_execucao


def test_janela_temporal_preserva_diferenca_de_probabilidade_de_madrugada():
    fim = INICIO + timedelta(days=7)

    baseline = criar_gerador(seed=321).gerar_registros(
        obter_cenario("baseline"),
        quantidade=5000,
        inicio=INICIO,
        fim=fim,
    )
    credential_attack = criar_gerador(seed=321).gerar_registros(
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


def test_profile_controla_mediana_do_valor_transacional():
    population_baixa = criar_populacao(
        "entidade-alpha",
        transaction_value_median=90.0,
        transaction_value_sigma=0.65,
    )
    population_alta = criar_populacao(
        "entidade-alpha",
        transaction_value_median=900.0,
        transaction_value_sigma=0.65,
    )

    registros_baixos = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_baixa,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_altos = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_alta,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    valores_baixos = [
        registro.observables["valor_transacao"] for registro in registros_baixos
    ]
    valores_altos = [
        registro.observables["valor_transacao"] for registro in registros_altos
    ]

    assert valores_baixos != valores_altos
    assert all(
        valor_alto > valor_baixo
        for valor_baixo, valor_alto in zip(
            valores_baixos,
            valores_altos,
            strict=True,
        )
    )


def test_profile_controla_dispersao_do_valor_transacional():
    population_estavel = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.10,
    )
    population_volatil = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=1.20,
    )

    registros_estaveis = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_estavel,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_volateis = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_volatil,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    valores_estaveis = [
        registro.observables["valor_transacao"] for registro in registros_estaveis
    ]
    valores_volateis = [
        registro.observables["valor_transacao"] for registro in registros_volateis
    ]

    assert valores_estaveis != valores_volateis


def test_mudar_apenas_baseline_transacional_nao_embaralha_evento():
    population_baixa = criar_populacao(
        "entidade-alpha",
        transaction_value_median=90.0,
        transaction_value_sigma=0.65,
    )
    population_alta = criar_populacao(
        "entidade-alpha",
        transaction_value_median=900.0,
        transaction_value_sigma=0.65,
    )

    registros_baixos = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_baixa,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_altos = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_alta,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    valores_baixos = [
        registro.observables["valor_transacao"] for registro in registros_baixos
    ]
    valores_altos = [
        registro.observables["valor_transacao"] for registro in registros_altos
    ]

    assert valores_baixos != valores_altos

    observaveis_baixos_sem_valor = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in registros_baixos
    ]
    observaveis_altos_sem_valor = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "valor_transacao"
        }
        for registro in registros_altos
    ]

    assert observaveis_baixos_sem_valor == observaveis_altos_sem_valor

    assert [registro.operational_labels for registro in registros_baixos] == [
        registro.operational_labels for registro in registros_altos
    ]

    assert [registro.truth for registro in registros_baixos] == [
        registro.truth for registro in registros_altos
    ]


def test_profile_controla_baseline_de_falhas_login():
    population_sem_falhas = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.0,
    )
    population_com_falhas = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=5.0,
    )

    registros_sem_falhas = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_sem_falhas,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_com_falhas = StatisticalGenerator(
        seed=42,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_com_falhas,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    falhas_sem_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in registros_sem_falhas
    ]
    falhas_com_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in registros_com_falhas
    ]

    assert all(falhas == 0 for falhas in falhas_sem_baseline)
    assert sum(falhas_com_baseline) > 0
    assert falhas_sem_baseline != falhas_com_baseline


def test_mudar_apenas_baseline_login_nao_embaralha_evento():
    population_sem_falhas = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=0.0,
    )
    population_com_falhas = criar_populacao(
        "entidade-alpha",
        transaction_value_median=180.0,
        transaction_value_sigma=0.65,
        recent_login_failure_rate=5.0,
    )

    registros_sem_falhas = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_sem_falhas,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    registros_com_falhas = StatisticalGenerator(
        seed=777,
        label_policy=POLITICA_SEM_RUIDO,
        population=population_com_falhas,
    ).gerar_registros(
        obter_cenario("baseline"),
        quantidade=50,
        inicio=INICIO,
        fim=FIM_PADRAO,
    )

    falhas_sem_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in registros_sem_falhas
    ]
    falhas_com_baseline = [
        registro.observables["falhas_login_recentes"]
        for registro in registros_com_falhas
    ]

    assert falhas_sem_baseline != falhas_com_baseline

    observaveis_sem_falhas_login = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "falhas_login_recentes"
        }
        for registro in registros_sem_falhas
    ]
    observaveis_com_falhas_login = [
        {
            campo: valor
            for campo, valor in registro.observables.items()
            if campo != "falhas_login_recentes"
        }
        for registro in registros_com_falhas
    ]

    assert observaveis_sem_falhas_login == observaveis_com_falhas_login

    assert [registro.operational_labels for registro in registros_sem_falhas] == [
        registro.operational_labels for registro in registros_com_falhas
    ]

    assert [registro.truth for registro in registros_sem_falhas] == [
        registro.truth for registro in registros_com_falhas
    ]
