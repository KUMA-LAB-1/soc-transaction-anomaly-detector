from dataclasses import FrozenInstanceError

import numpy as np
import pytest

from src.synthetic.seed_strategy import build_synthetic_seed_plan


def test_seed_plan_deriva_componentes_reproduziveis_e_distintos():
    primeiro = build_synthetic_seed_plan(42)
    segundo = build_synthetic_seed_plan(42)

    assert primeiro == segundo
    assert primeiro.root_seed == 42
    assert primeiro.statistical_seed != primeiro.population_seed


@pytest.mark.parametrize(
    "root_seed",
    (
        -1,
        True,
        1.5,
        "42",
        None,
    ),
)
def test_seed_plan_rejeita_root_seed_invalido(root_seed):
    with pytest.raises(ValueError, match="root_seed"):
        build_synthetic_seed_plan(root_seed)


def test_seed_plan_muda_componentes_quando_root_seed_muda():
    primeiro = build_synthetic_seed_plan(42)
    segundo = build_synthetic_seed_plan(43)

    assert primeiro.statistical_seed != segundo.statistical_seed
    assert primeiro.population_seed != segundo.population_seed


def test_seed_plan_aceita_root_seed_zero():
    plano = build_synthetic_seed_plan(0)

    assert plano.root_seed == 0
    assert isinstance(plano.statistical_seed, int)
    assert isinstance(plano.population_seed, int)


def test_synthetic_seed_plan_e_imutavel():
    plano = build_synthetic_seed_plan(42)

    with pytest.raises(FrozenInstanceError):
        plano.statistical_seed = 123


def test_seed_plan_preserva_namespaces_estaveis_dos_componentes():
    root_seed = 42
    plano = build_synthetic_seed_plan(root_seed)

    statistical_esperado = int(
        np.random.SeedSequence(
            root_seed,
            spawn_key=(0,),
        ).generate_state(
            1,
            dtype=np.uint64,
        )[0]
    )

    population_esperado = int(
        np.random.SeedSequence(
            root_seed,
            spawn_key=(1,),
        ).generate_state(
            1,
            dtype=np.uint64,
        )[0]
    )

    assert plano.statistical_seed == statistical_esperado
    assert plano.population_seed == population_esperado
