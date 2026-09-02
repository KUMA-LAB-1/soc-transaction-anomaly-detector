from dataclasses import replace

import pytest

from src.synthetic.scenarios import (
    CENARIOS_PADRAO,
    ScenarioDefinition,
    obter_cenario,
)


def test_catalogo_possui_cenarios_iniciais_esperados():
    assert set(CENARIOS_PADRAO) == {
        "baseline",
        "credential_attack",
        "account_takeover",
        "location_anomaly",
        "transaction_anomaly",
    }


def test_baseline_nao_e_ground_truth_suspeito():
    cenario = obter_cenario("baseline")

    assert cenario.name == "baseline"
    assert cenario.is_suspicious is False
    assert cenario.expected_mitre_techniques == ()


@pytest.mark.parametrize(
    "nome",
    [
        "credential_attack",
        "account_takeover",
        "location_anomaly",
        "transaction_anomaly",
    ],
)
def test_cenarios_anomalos_sao_ground_truth_suspeitos(nome):
    cenario = obter_cenario(nome)

    assert cenario.is_suspicious is True


def test_credential_attack_registra_expectativa_mitre_sem_expor_ao_modelo():
    cenario = obter_cenario("credential_attack")

    assert cenario.expected_mitre_techniques == ("T1110",)


def test_transaction_anomaly_nao_exige_tecnica_mitre():
    cenario = obter_cenario("transaction_anomaly")

    assert cenario.is_suspicious is True
    assert cenario.expected_mitre_techniques == ()


@pytest.mark.parametrize(
    "nome",
    CENARIOS_PADRAO,
)
def test_probabilidades_dos_cenarios_estao_no_intervalo_valido(nome):
    cenario = obter_cenario(nome)

    probabilidades = (
        cenario.probabilidade_madrugada,
        cenario.probabilidade_dispositivo_novo,
        cenario.probabilidade_alteracao_limite,
        cenario.probabilidade_mudanca_localizacao,
    )

    assert all(0.0 <= valor <= 1.0 for valor in probabilidades)


@pytest.mark.parametrize(
    "nome",
    CENARIOS_PADRAO,
)
def test_nenhum_cenario_deterministico_entrega_sinais_booleanos(nome):
    cenario = obter_cenario(nome)

    probabilidades = (
        cenario.probabilidade_madrugada,
        cenario.probabilidade_dispositivo_novo,
        cenario.probabilidade_alteracao_limite,
        cenario.probabilidade_mudanca_localizacao,
    )

    assert all(0.0 < valor < 1.0 for valor in probabilidades)


@pytest.mark.parametrize(
    "nome",
    CENARIOS_PADRAO,
)
def test_parametros_numericos_possuem_variabilidade(nome):
    cenario = obter_cenario(nome)

    assert cenario.valor_mediano > 0
    assert cenario.valor_sigma > 0
    assert cenario.media_falhas_login >= 0


def test_cenarios_normais_e_suspeitos_possuem_distribuicoes_sobrepostas():
    baseline = obter_cenario("baseline")
    suspeito = obter_cenario("transaction_anomaly")

    assert baseline.valor_sigma > 0
    assert suspeito.valor_sigma > 0

    assert baseline.probabilidade_madrugada > 0
    assert suspeito.probabilidade_madrugada < 1

    assert baseline.probabilidade_dispositivo_novo > 0
    assert suspeito.probabilidade_dispositivo_novo < 1


def test_obter_cenario_rejeita_nome_desconhecido():
    with pytest.raises(ValueError, match="Cenário sintético desconhecido"):
        obter_cenario("vampiro_de_capa_preta")


def test_scenario_definition_rejeita_probabilidade_invalida():
    with pytest.raises(ValueError, match="probabilidade"):
        ScenarioDefinition(
            name="cenario-invalido",
            is_suspicious=True,
            valor_mediano=100.0,
            valor_sigma=0.5,
            media_falhas_login=1.0,
            probabilidade_madrugada=1.5,
            probabilidade_dispositivo_novo=0.5,
            probabilidade_alteracao_limite=0.5,
            probabilidade_mudanca_localizacao=0.5,
        )


def test_scenario_definition_rejeita_parametros_numericos_invalidos():
    with pytest.raises(ValueError, match="valor_mediano"):
        ScenarioDefinition(
            name="cenario-invalido",
            is_suspicious=False,
            valor_mediano=0.0,
            valor_sigma=0.5,
            media_falhas_login=0.0,
            probabilidade_madrugada=0.1,
            probabilidade_dispositivo_novo=0.1,
            probabilidade_alteracao_limite=0.1,
            probabilidade_mudanca_localizacao=0.1,
        )


@pytest.mark.parametrize(
    ("campo", "valor_invalido", "mensagem_esperada"),
    [
        ("valor_sigma", 0.0, "valor_sigma"),
        ("media_falhas_login", -0.1, "media_falhas_login"),
    ],
)
def test_scenario_definition_rejeita_demais_parametros_numericos_invalidos(
    campo,
    valor_invalido,
    mensagem_esperada,
):
    cenario = obter_cenario("baseline")

    with pytest.raises(ValueError, match=mensagem_esperada):
        replace(
            cenario,
            **{campo: valor_invalido},
        )
