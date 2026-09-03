from src.synthetic.allocation import allocate_scenario_quantities


def test_alocacao_compartilhada_preserva_maior_resto():
    quantidades = allocate_scenario_quantities(
        [1 / 3, 1 / 3, 1 / 3],
        quantidade=10,
    )

    assert quantidades == (4, 3, 3)


def test_alocacao_compartilhada_preserva_proporcao_exata():
    quantidades = allocate_scenario_quantities(
        [0.80, 0.20],
        quantidade=100,
    )

    assert quantidades == (80, 20)


def test_alocacao_compartilhada_permite_cenario_com_zero_registros():
    quantidades = allocate_scenario_quantities(
        [0.99, 0.01],
        quantidade=1,
    )

    assert quantidades == (1, 0)
