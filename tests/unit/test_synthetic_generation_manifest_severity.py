import math
from dataclasses import FrozenInstanceError

import pytest

from src.synthetic.generation_manifest import SeverityPolicyManifest


def test_severity_policy_manifest_preserva_snapshot_da_politica():
    manifest = SeverityPolicyManifest(
        normal_min=0.0,
        normal_max=35.0,
        suspicious_min=65.0,
        suspicious_max=100.0,
    )

    assert manifest.normal_min == 0.0
    assert manifest.normal_max == 35.0
    assert manifest.suspicious_min == 65.0
    assert manifest.suspicious_max == 100.0


@pytest.mark.parametrize(
    "campo",
    (
        "normal_min",
        "normal_max",
        "suspicious_min",
        "suspicious_max",
    ),
)
@pytest.mark.parametrize(
    "valor_invalido",
    (
        -0.1,
        100.1,
        math.nan,
        math.inf,
        -math.inf,
        True,
        "50.0",
        None,
    ),
)
def test_severity_policy_manifest_rejeita_valor_fora_do_dominio(
    campo,
    valor_invalido,
):
    valores = {
        "normal_min": 0.0,
        "normal_max": 35.0,
        "suspicious_min": 65.0,
        "suspicious_max": 100.0,
    }
    valores[campo] = valor_invalido

    with pytest.raises(ValueError, match=campo):
        SeverityPolicyManifest(**valores)


@pytest.mark.parametrize(
    ("valores", "campo_esperado"),
    (
        (
            {
                "normal_min": 40.0,
                "normal_max": 35.0,
                "suspicious_min": 65.0,
                "suspicious_max": 100.0,
            },
            "normal_min",
        ),
        (
            {
                "normal_min": 0.0,
                "normal_max": 35.0,
                "suspicious_min": 80.0,
                "suspicious_max": 70.0,
            },
            "suspicious_min",
        ),
    ),
)
def test_severity_policy_manifest_rejeita_intervalo_invertido(
    valores,
    campo_esperado,
):
    with pytest.raises(ValueError, match=campo_esperado):
        SeverityPolicyManifest(**valores)


def test_severity_policy_manifest_aceita_intervalos_degenerados():
    manifest = SeverityPolicyManifest(
        normal_min=20.0,
        normal_max=20.0,
        suspicious_min=80.0,
        suspicious_max=80.0,
    )

    assert manifest.normal_min == manifest.normal_max == 20.0
    assert manifest.suspicious_min == manifest.suspicious_max == 80.0


def test_severity_policy_manifest_e_imutavel():
    manifest = SeverityPolicyManifest(
        normal_min=0.0,
        normal_max=35.0,
        suspicious_min=65.0,
        suspicious_max=100.0,
    )

    with pytest.raises(FrozenInstanceError):
        manifest.normal_min = 10.0


def test_build_severity_policy_manifest_cria_snapshot_da_policy():
    from src.synthetic.generation_manifest_builder import (
        build_severity_policy_manifest,
    )
    from src.synthetic.severity import SeverityPolicy

    policy = SeverityPolicy(
        normal_min=0.0,
        normal_max=35.0,
        suspicious_min=65.0,
        suspicious_max=100.0,
    )

    manifest = build_severity_policy_manifest(policy)

    assert manifest.normal_min == policy.normal_min
    assert manifest.normal_max == policy.normal_max
    assert manifest.suspicious_min == policy.suspicious_min
    assert manifest.suspicious_max == policy.suspicious_max
    assert manifest is not policy


@pytest.mark.parametrize(
    "policy",
    (
        123,
        "severity-policy",
        object(),
        None,
    ),
)
def test_build_severity_policy_manifest_rejeita_policy_invalida(
    policy,
):
    from src.synthetic.generation_manifest_builder import (
        build_severity_policy_manifest,
    )

    with pytest.raises(ValueError, match="policy"):
        build_severity_policy_manifest(policy)
