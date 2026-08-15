import numpy as np
import pandas as pd
import pytest

from src.models.anomaly_detection import executar_detectores_anomalia

pytestmark = pytest.mark.filterwarnings(
    "ignore:The covariance matrix associated to your dataset is not full rank:UserWarning"
)


def criar_dataset_anomalias() -> pd.DataFrame:
    registros = []

    for i in range(60):
        suspeita = i % 10 == 0

        registros.append(
            {
                "status_transacao": (
                    "Bloqueada por Suspeita" if suspeita else "Aprovada"
                ),
                "valor_transacao": 5000.0 if suspeita else 100.0 + i,
                "hora": 3 if suspeita else i % 24,
                "zscore_valor_cliente": 5.0 if suspeita else 0.2,
                "qtd_transacoes_anteriores": i,
                "falhas_login_recentes": 4 if suspeita else 0,
                "dispositivo_novo_flag": suspeita,
                "alteracao_limite_flag": suspeita,
                "mudanca_localizacao_flag": False,
            }
        )

    return pd.DataFrame(registros)


def test_executar_detectores_retorna_quatro_resultados():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    nomes = {item["modelo"] for item in resultado["resultados"]}

    assert nomes == {
        "isolation_forest",
        "local_outlier_factor",
        "one_class_svm",
        "elliptic_envelope",
    }


def test_contamination_respeita_teto_pratico():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    assert resultado["contamination"] <= 0.15
    assert resultado["contamination"] > 0


def test_taxa_suspeita_real_corresponde_ao_dataset():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    assert resultado["taxa_suspeita_real"] == 0.1


def test_detectores_validos_retornam_metricas():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    validos = [item for item in resultado["resultados"] if item["status"] == "ok"]

    assert validos

    for item in validos:
        assert 0 <= item["precision_vs_status_real"] <= 1
        assert 0 <= item["recall_vs_status_real"] <= 1
        assert 0 <= item["f1_vs_status_real"] <= 1
        assert item["qtd_anomalias"] >= 0
        assert 0 <= item["taxa_anomalias"] <= 1
        assert item["tempo_segundos"] >= 0


def test_predicoes_tem_mesmo_tamanho_do_dataset():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    for nome, predicoes in resultado["predicoes"].items():
        assert nome in resultado["modelos"]
        assert len(predicoes["predicao_original"]) == len(df)
        assert len(predicoes["score_original"]) == len(df)


def test_predicoes_usam_convencao_normal_e_anomalia():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    for predicoes in resultado["predicoes"].values():
        valores = set(np.unique(predicoes["predicao_original"]))

        assert valores.issubset({-1, 1})


def test_features_usadas_sao_as_disponiveis_no_dataset():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    validos = [item for item in resultado["resultados"] if item["status"] == "ok"]

    features_esperadas = {
        "valor_transacao",
        "hora",
        "zscore_valor_cliente",
        "qtd_transacoes_anteriores",
        "falhas_login_recentes",
        "dispositivo_novo_flag",
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    }

    for item in validos:
        assert set(item["features"]) == features_esperadas


def test_falha_de_um_detector_nao_interrompe_os_demais(monkeypatch):
    df = criar_dataset_anomalias()

    def falhar_ao_treinar(*args, **kwargs):
        raise RuntimeError("falha simulada")

    monkeypatch.setattr(
        "src.models.anomaly_detection.IsolationForest.fit",
        falhar_ao_treinar,
    )

    resultado = executar_detectores_anomalia(df)

    resultados_por_modelo = {item["modelo"]: item for item in resultado["resultados"]}

    isolation = resultados_por_modelo["isolation_forest"]

    assert isolation["status"] == "erro"
    assert "falha simulada" in isolation["erro"]

    assert resultados_por_modelo["local_outlier_factor"]["status"] == "ok"
    assert resultados_por_modelo["one_class_svm"]["status"] == "ok"
    assert resultados_por_modelo["elliptic_envelope"]["status"] == "ok"
