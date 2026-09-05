import pytest

from src.synthetic.quality import empirical_cdf_distance


def test_empirical_cdf_distance_calcula_separacao_parcial():
    left = (1.0, 2.0, 3.0, 4.0)
    right = (3.0, 4.0, 5.0, 6.0)

    result = empirical_cdf_distance(left, right)

    assert result == pytest.approx(0.50)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ((), (1.0, 2.0, 3.0)),
        ((1.0, 2.0, 3.0), ()),
    ],
)
def test_empirical_cdf_distance_rejeita_amostra_vazia(left, right):
    with pytest.raises(ValueError, match="amostras não podem ser vazias"):
        empirical_cdf_distance(left, right)


def test_empirical_cdf_distance_retorna_zero_para_distribuicoes_iguais():
    values = (1.0, 2.0, 3.0, 4.0)

    result = empirical_cdf_distance(values, values)

    assert result == pytest.approx(0.0)


def test_empirical_cdf_distance_retorna_um_para_distribuicoes_separadas():
    left = (1.0, 2.0, 3.0)
    right = (4.0, 5.0, 6.0)

    result = empirical_cdf_distance(left, right)

    assert result == pytest.approx(1.0)


def test_empirical_cdf_distance_lida_com_valores_repetidos():
    left = (0.0, 0.0, 0.0, 1.0)
    right = (0.0, 1.0, 1.0, 1.0)

    result = empirical_cdf_distance(left, right)

    assert result == pytest.approx(0.50)


@pytest.mark.parametrize(
    ("left", "right"),
    [
        ((1.0, float("nan"), 3.0), (1.0, 2.0, 3.0)),
        ((1.0, float("inf"), 3.0), (1.0, 2.0, 3.0)),
        ((1.0, float("-inf"), 3.0), (1.0, 2.0, 3.0)),
        ((1.0, 2.0, 3.0), (1.0, float("nan"), 3.0)),
        ((1.0, 2.0, 3.0), (1.0, float("inf"), 3.0)),
        ((1.0, 2.0, 3.0), (1.0, float("-inf"), 3.0)),
    ],
)
def test_empirical_cdf_distance_rejeita_valores_nao_finitos(left, right):
    with pytest.raises(
        ValueError,
        match="amostras devem conter apenas valores finitos",
    ):
        empirical_cdf_distance(left, right)
