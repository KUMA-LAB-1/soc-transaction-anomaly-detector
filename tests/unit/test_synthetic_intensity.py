import pytest

from src.synthetic.intensity import EventIntensityPolicy


def test_event_intensity_policy_mapeia_sorteio_para_intervalo():
    policy = EventIntensityPolicy(
        intensity_min=0.20,
        intensity_max=0.80,
    )

    intensidade = policy.gerar_intensidade(
        sorteio=0.50,
    )

    assert intensidade == pytest.approx(0.50)


@pytest.mark.parametrize(
    (
        "sorteio",
        "esperado",
    ),
    [
        (0.0, 0.20),
        (1.0, 0.80),
    ],
)
def test_event_intensity_policy_preserva_extremos_do_intervalo(
    sorteio,
    esperado,
):
    policy = EventIntensityPolicy(
        intensity_min=0.20,
        intensity_max=0.80,
    )

    assert policy.gerar_intensidade(
        sorteio=sorteio,
    ) == pytest.approx(esperado)


def test_event_intensity_policy_permite_intervalo_degenerado():
    policy = EventIntensityPolicy(
        intensity_min=0.60,
        intensity_max=0.60,
    )

    assert policy.gerar_intensidade(
        sorteio=0.25,
    ) == pytest.approx(0.60)


@pytest.mark.parametrize(
    (
        "intensity_min",
        "intensity_max",
    ),
    [
        (-0.01, 0.80),
        (0.20, 1.01),
        (float("nan"), 0.80),
        (0.20, float("inf")),
        (True, 0.80),
        (0.20, False),
        ("0.20", 0.80),
        (0.20, None),
    ],
)
def test_event_intensity_policy_rejeita_limites_invalidos(
    intensity_min,
    intensity_max,
):
    with pytest.raises(
        ValueError,
        match="intensity_",
    ):
        EventIntensityPolicy(
            intensity_min=intensity_min,
            intensity_max=intensity_max,
        )


def test_event_intensity_policy_rejeita_intervalo_invertido():
    with pytest.raises(
        ValueError,
        match="intensity_min",
    ):
        EventIntensityPolicy(
            intensity_min=0.80,
            intensity_max=0.20,
        )


@pytest.mark.parametrize(
    "sorteio",
    [
        -0.01,
        1.01,
        float("nan"),
        float("inf"),
        float("-inf"),
        True,
        "0.5",
        None,
    ],
)
def test_event_intensity_policy_rejeita_sorteio_invalido(sorteio):
    policy = EventIntensityPolicy(
        intensity_min=0.20,
        intensity_max=0.80,
    )

    with pytest.raises(
        ValueError,
        match="sorteio",
    ):
        policy.gerar_intensidade(
            sorteio=sorteio,
        )
