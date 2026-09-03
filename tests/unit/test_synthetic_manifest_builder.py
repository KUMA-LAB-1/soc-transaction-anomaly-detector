from datetime import datetime

from src.synthetic.composer import ScenarioMix
from src.synthetic.label_policy import OperationalLabelPolicy
from src.synthetic.manifest import LabelPolicyManifest, ScenarioManifestEntry
from src.synthetic.manifest_builder import build_dataset_manifest
from src.synthetic.scenarios import obter_cenario


def test_build_dataset_manifest_cria_snapshot_da_configuracao_operacional():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=1 / 3,
        ),
        ScenarioMix(
            cenario=obter_cenario("credential_attack"),
            proporcao=1 / 3,
        ),
        ScenarioMix(
            cenario=obter_cenario("account_takeover"),
            proporcao=1 / 3,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.20,
        probabilidade_falso_negativo=0.30,
    )

    manifest = build_dataset_manifest(
        seed=42,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
    )

    assert manifest.schema_version == "1"
    assert manifest.seed == 42
    assert manifest.quantidade == 10
    assert manifest.inicio == inicio
    assert manifest.fim == fim

    assert manifest.scenarios == (
        ScenarioManifestEntry(
            scenario="baseline",
            configured_proportion=1 / 3,
            allocated_quantity=4,
        ),
        ScenarioManifestEntry(
            scenario="credential_attack",
            configured_proportion=1 / 3,
            allocated_quantity=3,
        ),
        ScenarioManifestEntry(
            scenario="account_takeover",
            configured_proportion=1 / 3,
            allocated_quantity=3,
        ),
    )

    assert manifest.label_policy == LabelPolicyManifest(
        false_positive_probability=0.20,
        false_negative_probability=0.30,
    )


def test_build_dataset_manifest_preserva_cenario_com_alocacao_zero():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    misturas = [
        ScenarioMix(
            cenario=obter_cenario("baseline"),
            proporcao=0.99,
        ),
        ScenarioMix(
            cenario=obter_cenario("credential_attack"),
            proporcao=0.01,
        ),
    ]

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.0,
        probabilidade_falso_negativo=0.0,
    )

    manifest = build_dataset_manifest(
        seed=42,
        quantidade=1,
        inicio=inicio,
        fim=fim,
        misturas=misturas,
        label_policy=label_policy,
    )

    assert manifest.scenarios == (
        ScenarioManifestEntry(
            scenario="baseline",
            configured_proportion=0.99,
            allocated_quantity=1,
        ),
        ScenarioManifestEntry(
            scenario="credential_attack",
            configured_proportion=0.01,
            allocated_quantity=0,
        ),
    )


def test_build_dataset_manifest_converte_label_policy_em_snapshot_independente():
    inicio = datetime(2026, 1, 1, 0, 0)
    fim = datetime(2026, 1, 8, 0, 0)

    label_policy = OperationalLabelPolicy(
        probabilidade_falso_positivo=0.20,
        probabilidade_falso_negativo=0.30,
    )

    manifest = build_dataset_manifest(
        seed=42,
        quantidade=10,
        inicio=inicio,
        fim=fim,
        misturas=[
            ScenarioMix(
                cenario=obter_cenario("baseline"),
                proporcao=1.0,
            ),
        ],
        label_policy=label_policy,
    )

    assert isinstance(manifest.label_policy, LabelPolicyManifest)
    assert not isinstance(manifest.label_policy, OperationalLabelPolicy)
    assert manifest.label_policy.false_positive_probability == 0.20
    assert manifest.label_policy.false_negative_probability == 0.30
