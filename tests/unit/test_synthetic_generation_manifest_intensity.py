import math
from dataclasses import FrozenInstanceError

import pytest


def test_event_intensity_policy_manifest_preserva_snapshot_da_politica():
    from src.synthetic.generation_manifest import EventIntensityPolicyManifest

    manifest = EventIntensityPolicyManifest(
        intensity_min=0.2,
        intensity_max=0.8,
    )

    assert manifest.intensity_min == 0.2
    assert manifest.intensity_max == 0.8


@pytest.mark.parametrize(
    "campo",
    (
        "intensity_min",
        "intensity_max",
    ),
)
@pytest.mark.parametrize(
    "valor_invalido",
    (
        -0.1,
        1.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "0.5",
        None,
    ),
)
def test_event_intensity_policy_manifest_rejeita_valor_fora_do_dominio(
    campo,
    valor_invalido,
):
    valores = {
        "intensity_min": 0.2,
        "intensity_max": 0.8,
    }
    valores[campo] = valor_invalido

    from src.synthetic.generation_manifest import EventIntensityPolicyManifest

    with pytest.raises(ValueError, match=campo):
        EventIntensityPolicyManifest(**valores)


def test_event_intensity_policy_manifest_rejeita_intervalo_invertido():
    from src.synthetic.generation_manifest import EventIntensityPolicyManifest

    with pytest.raises(ValueError, match="intensity_min"):
        EventIntensityPolicyManifest(
            intensity_min=0.8,
            intensity_max=0.2,
        )


def test_event_intensity_policy_manifest_aceita_intervalo_degenerado():
    from src.synthetic.generation_manifest import EventIntensityPolicyManifest

    manifest = EventIntensityPolicyManifest(
        intensity_min=0.5,
        intensity_max=0.5,
    )

    assert manifest.intensity_min == manifest.intensity_max == 0.5


def test_event_intensity_policy_manifest_e_imutavel():
    from src.synthetic.generation_manifest import EventIntensityPolicyManifest

    manifest = EventIntensityPolicyManifest(
        intensity_min=0.2,
        intensity_max=0.8,
    )

    with pytest.raises(FrozenInstanceError):
        manifest.intensity_min = 0.4


def test_build_event_intensity_policy_manifest_cria_snapshot_da_policy():
    from src.synthetic.generation_manifest_builder import (
        build_event_intensity_policy_manifest,
    )
    from src.synthetic.intensity import EventIntensityPolicy

    policy = EventIntensityPolicy(
        intensity_min=0.2,
        intensity_max=0.8,
    )

    manifest = build_event_intensity_policy_manifest(policy)

    assert manifest.intensity_min == policy.intensity_min
    assert manifest.intensity_max == policy.intensity_max
    assert manifest is not policy


@pytest.mark.parametrize(
    "policy",
    (
        123,
        "intensity-policy",
        object(),
        None,
    ),
)
def test_build_event_intensity_policy_manifest_rejeita_policy_invalida(
    policy,
):
    from src.synthetic.generation_manifest_builder import (
        build_event_intensity_policy_manifest,
    )

    with pytest.raises(ValueError, match="policy"):
        build_event_intensity_policy_manifest(policy)
