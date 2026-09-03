import math

import pytest

from src.synthetic.label_policy import OperationalLabelPolicy


@pytest.mark.parametrize(
    ("falso_positivo", "falso_negativo"),
    [
        (math.nan, 0.10),
        (0.10, math.nan),
        (math.inf, 0.10),
        (0.10, math.inf),
        (-math.inf, 0.10),
        (0.10, -math.inf),
    ],
)
def test_politica_rejeita_probabilidades_nao_finitas(
    falso_positivo,
    falso_negativo,
):
    with pytest.raises(ValueError, match="probabilidade"):
        OperationalLabelPolicy(
            probabilidade_falso_positivo=falso_positivo,
            probabilidade_falso_negativo=falso_negativo,
        )


@pytest.mark.parametrize(
    "is_suspicious",
    [
        0,
        1,
        "sim",
        None,
    ],
)
def test_gerar_status_rejeita_truth_que_nao_e_bool(is_suspicious):
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.10,
        probabilidade_falso_negativo=0.10,
    )

    with pytest.raises(ValueError, match="is_suspicious"):
        politica.gerar_status(
            is_suspicious=is_suspicious,
            sorteio=0.50,
        )


@pytest.mark.parametrize(
    "sorteio",
    [
        -0.01,
        1.0,
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
def test_gerar_status_rejeita_sorteio_invalido(sorteio):
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.10,
        probabilidade_falso_negativo=0.10,
    )

    with pytest.raises(ValueError, match="sorteio"):
        politica.gerar_status(
            is_suspicious=False,
            sorteio=sorteio,
        )


@pytest.mark.parametrize(
    ("falso_positivo", "falso_negativo"),
    [
        (-0.01, 0.10),
        (1.01, 0.10),
        (0.10, -0.01),
        (0.10, 1.01),
    ],
)
def test_politica_rejeita_probabilidades_fora_do_intervalo(
    falso_positivo,
    falso_negativo,
):
    with pytest.raises(ValueError, match="probabilidade"):
        OperationalLabelPolicy(
            probabilidade_falso_positivo=falso_positivo,
            probabilidade_falso_negativo=falso_negativo,
        )


def test_politica_aceita_probabilidades_nos_limites():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=1.0,
    )

    assert politica.probabilidade_falso_positivo == 0.0
    assert politica.probabilidade_falso_negativo == 1.0


@pytest.mark.parametrize(
    ("falso_positivo", "falso_negativo"),
    [
        (True, 0.10),
        (False, 0.10),
        (0.10, True),
        (0.10, False),
        ("0.10", 0.10),
        (0.10, "0.10"),
        (None, 0.10),
        (0.10, None),
    ],
)
def test_politica_rejeita_probabilidades_que_nao_sao_numericas_validas(
    falso_positivo,
    falso_negativo,
):
    with pytest.raises(ValueError, match="probabilidade"):
        OperationalLabelPolicy(
            probabilidade_falso_positivo=falso_positivo,
            probabilidade_falso_negativo=falso_negativo,
        )


def test_sem_falso_positivo_registro_normal_permanece_concluido():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    status = politica.gerar_status(
        is_suspicious=False,
        sorteio=0.0,
    )

    assert status == "Concluída"


def test_falso_positivo_certo_envia_registro_normal_para_analise():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=1.0,
        probabilidade_falso_negativo=0.0,
    )

    status = politica.gerar_status(
        is_suspicious=False,
        sorteio=0.99,
    )

    assert status == "Em Análise"


def test_sem_falso_negativo_registro_suspeito_permanece_em_analise():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    status = politica.gerar_status(
        is_suspicious=True,
        sorteio=0.0,
    )

    assert status == "Em Análise"


def test_falso_negativo_certo_libera_registro_suspeito():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=1.0,
    )

    status = politica.gerar_status(
        is_suspicious=True,
        sorteio=0.99,
    )

    assert status == "Concluída"


def test_falso_positivo_nao_dispara_quando_sorteio_iguala_probabilidade():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.25,
        probabilidade_falso_negativo=0.0,
    )

    status = politica.gerar_status(
        is_suspicious=False,
        sorteio=0.25,
    )

    assert status == "Concluída"


def test_falso_negativo_nao_dispara_quando_sorteio_iguala_probabilidade():
    politica = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.25,
    )

    status = politica.gerar_status(
        is_suspicious=True,
        sorteio=0.25,
    )

    assert status == "Em Análise"
