import pytest

from src.synthetic.severity import SeverityPolicy


def test_severity_policy_mapeia_sorteio_para_faixa_normal():
    policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    score = policy.gerar_score(
        is_suspicious=False,
        sorteio=0.5,
    )

    assert score == pytest.approx(20.0)


def test_severity_policy_mapeia_sorteio_para_faixa_suspeita():
    policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    score = policy.gerar_score(
        is_suspicious=True,
        sorteio=0.5,
    )

    assert score == pytest.approx(60.0)


def test_severity_policy_permite_sobreposicao_entre_faixas():
    policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=60.0,
        suspicious_min=40.0,
        suspicious_max=100.0,
    )

    assert policy.normal_max > policy.suspicious_min


@pytest.mark.parametrize(
    (
        "campo",
        "valor",
    ),
    [
        ("normal_min", -0.01),
        ("normal_max", 100.01),
        ("suspicious_min", float("nan")),
        ("suspicious_max", float("inf")),
        ("normal_min", True),
        ("suspicious_max", "100"),
    ],
)
def test_severity_policy_rejeita_faixa_invalida(campo, valor):
    parametros = {
        "normal_min": 0.0,
        "normal_max": 40.0,
        "suspicious_min": 20.0,
        "suspicious_max": 100.0,
    }
    parametros[campo] = valor

    with pytest.raises(
        ValueError,
        match=campo,
    ):
        SeverityPolicy(**parametros)


@pytest.mark.parametrize(
    "parametros",
    [
        {
            "normal_min": 60.0,
            "normal_max": 40.0,
            "suspicious_min": 20.0,
            "suspicious_max": 100.0,
        },
        {
            "normal_min": 0.0,
            "normal_max": 40.0,
            "suspicious_min": 90.0,
            "suspicious_max": 70.0,
        },
    ],
)
def test_severity_policy_rejeita_intervalo_invertido(parametros):
    with pytest.raises(
        ValueError,
        match="min",
    ):
        SeverityPolicy(**parametros)


@pytest.mark.parametrize(
    "is_suspicious",
    [
        1,
        0,
        "true",
        None,
    ],
)
def test_severity_policy_rejeita_is_suspicious_invalido(is_suspicious):
    policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    with pytest.raises(
        ValueError,
        match="is_suspicious",
    ):
        policy.gerar_score(
            is_suspicious=is_suspicious,
            sorteio=0.5,
        )


@pytest.mark.parametrize(
    "sorteio",
    [
        -0.01,
        1.01,
        float("inf"),
        float("-inf"),
        float("nan"),
        True,
        "0.5",
    ],
)
def test_severity_policy_rejeita_sorteio_invalido(sorteio):
    policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    with pytest.raises(
        ValueError,
        match="sorteio",
    ):
        policy.gerar_score(
            is_suspicious=True,
            sorteio=sorteio,
        )


@pytest.mark.parametrize(
    (
        "sorteio",
        "esperado",
    ),
    [
        (0.0, 20.0),
        (1.0, 100.0),
    ],
)
def test_severity_policy_aceita_limites_do_sorteio(
    sorteio,
    esperado,
):
    policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=40.0,
        suspicious_min=20.0,
        suspicious_max=100.0,
    )

    assert policy.gerar_score(
        is_suspicious=True,
        sorteio=sorteio,
    ) == pytest.approx(esperado)
