from datetime import datetime

import pytest

from src.synthetic.contracts import GenerationTruth, SyntheticRecord
from src.synthetic.firewall import (
    projetar_dataset_modelagem,
    projetar_ground_truth,
)


def criar_registro_sintetico() -> SyntheticRecord:
    return SyntheticRecord(
        observables={
            "id_transacao": 1,
            "cliente_pseudonimo": "cliente-001",
            "data_hora_transacao": datetime(2026, 1, 10, 14, 30),
            "tipo_transacao": "Pix",
            "valor_transacao": 275.50,
            "falhas_login_recentes": 1,
            "dispositivo_novo_flag": False,
            "alteracao_limite_flag": False,
            "mudanca_localizacao_flag": False,
        },
        operational_labels={
            "status_transacao": "Concluída",
        },
        truth=GenerationTruth(
            scenario="credential_attack",
            is_suspicious=True,
            attack_profile="credential_attack",
            expected_mitre_techniques=("T1110",),
        ),
    )


def test_dataset_modelagem_nao_expoe_ground_truth():
    registro = criar_registro_sintetico()

    resultado = projetar_dataset_modelagem([registro])

    assert resultado.loc[0, "id_transacao"] == 1
    assert resultado.loc[0, "valor_transacao"] == 275.50
    assert resultado.loc[0, "status_transacao"] == "Concluída"

    assert "scenario" not in resultado.columns
    assert "is_suspicious" not in resultado.columns
    assert "attack_profile" not in resultado.columns
    assert "expected_mitre_techniques" not in resultado.columns


def test_label_operacional_pode_divergir_do_ground_truth():
    registro = criar_registro_sintetico()

    dataset_modelagem = projetar_dataset_modelagem([registro])
    ground_truth = projetar_ground_truth([registro])

    assert dataset_modelagem.loc[0, "status_transacao"] == "Concluída"
    assert bool(ground_truth.loc[0, "is_suspicious"]) is True


def test_ground_truth_possui_projecao_separada_para_avaliacao():
    registro = criar_registro_sintetico()

    resultado = projetar_ground_truth([registro])

    assert resultado.loc[0, "id_transacao"] == 1
    assert resultado.loc[0, "scenario"] == "credential_attack"
    assert bool(resultado.loc[0, "is_suspicious"]) is True
    assert resultado.loc[0, "attack_profile"] == "credential_attack"
    assert resultado.loc[0, "expected_mitre_techniques"] == ("T1110",)


@pytest.mark.parametrize(
    "campo_reservado",
    [
        "scenario",
        "is_suspicious",
        "attack_profile",
        "expected_mitre_techniques",
    ],
)
def test_firewall_rejeita_ground_truth_injetado_nos_observaveis(
    campo_reservado,
):
    registro = criar_registro_sintetico()

    observables = dict(registro.observables)
    observables[campo_reservado] = "valor-invalido"

    registro_contaminado = SyntheticRecord(
        observables=observables,
        operational_labels=registro.operational_labels,
        truth=registro.truth,
    )

    with pytest.raises(ValueError, match="ground truth"):
        projetar_dataset_modelagem([registro_contaminado])


def test_firewall_rejeita_colisao_entre_observavel_e_label_operacional():
    registro = criar_registro_sintetico()

    observables = dict(registro.observables)
    observables["status_transacao"] = "Bloqueada por Suspeita"

    registro_contaminado = SyntheticRecord(
        observables=observables,
        operational_labels=registro.operational_labels,
        truth=registro.truth,
    )

    with pytest.raises(ValueError, match="colisão"):
        projetar_dataset_modelagem([registro_contaminado])


def test_firewall_rejeita_ground_truth_injetado_nos_labels_operacionais():
    registro = criar_registro_sintetico()

    labels = dict(registro.operational_labels)
    labels["is_suspicious"] = True

    registro_contaminado = SyntheticRecord(
        observables=registro.observables,
        operational_labels=labels,
        truth=registro.truth,
    )

    with pytest.raises(ValueError, match="ground truth"):
        projetar_dataset_modelagem([registro_contaminado])
