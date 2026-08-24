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
                "data_hora_transacao": (
                    pd.Timestamp("2026-01-01") + pd.Timedelta(hours=i)
                ),
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


def test_contamination_padrao_usa_politica_operacional():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    assert resultado["contamination"] == pytest.approx(0.15)


def test_contamination_pode_ser_configurada_explicitamente():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(
        df,
        contamination=0.05,
    )

    assert resultado["contamination"] == pytest.approx(0.05)

    validos = [item for item in resultado["resultados"] if item["status"] == "ok"]

    for item in validos:
        assert item["contamination_usado"] == pytest.approx(0.05)


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


def test_anomaly_mantem_in_sample_por_padrao():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(df)

    assert resultado["estrategia_validacao"] == "in_sample"
    assert resultado["n_treino"] == len(df)
    assert resultado["n_avaliacao"] == len(df)


def test_anomaly_suporta_validacao_temporal():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(
        df,
        estrategia_validacao="temporal",
    )

    assert resultado["estrategia_validacao"] == "temporal"
    assert resultado["n_treino"] == 45
    assert resultado["n_avaliacao"] == 15


def test_anomaly_temporal_prediz_apenas_futuro():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(
        df,
        estrategia_validacao="temporal",
    )

    for predicoes in resultado["predicoes"].values():
        assert len(predicoes["predicao_original"]) == 15
        assert len(predicoes["score_original"]) == 15


def test_anomaly_temporal_avaliacao_usa_futuro():
    df = criar_dataset_anomalias()

    resultado = executar_detectores_anomalia(
        df,
        estrategia_validacao="temporal",
    )

    indices_treino = resultado["indices_treino"]
    indices_avaliacao = resultado["indices_avaliacao"]

    timestamps = pd.to_datetime(df["data_hora_transacao"])

    assert (
        timestamps.iloc[indices_treino].max()
        <= timestamps.iloc[indices_avaliacao].min()
    )


def test_anomaly_rejeita_estrategia_desconhecida():
    df = criar_dataset_anomalias()

    with pytest.raises(
        ValueError,
        match="estrategia_validacao",
    ):
        executar_detectores_anomalia(
            df,
            estrategia_validacao="magia_verde",
        )


def test_contamination_nao_depende_de_status_transacao():
    df = criar_dataset_anomalias()

    resultado_original = executar_detectores_anomalia(
        df,
        estrategia_validacao="temporal",
        contamination=0.07,
    )

    df_alterado = df.copy()
    df_alterado["status_transacao"] = "Bloqueada por Suspeita"

    resultado_alterado = executar_detectores_anomalia(
        df_alterado,
        estrategia_validacao="temporal",
        contamination=0.07,
    )

    assert resultado_alterado["contamination"] == pytest.approx(
        resultado_original["contamination"]
    )

    assert resultado_alterado["taxa_suspeita_real"] != pytest.approx(
        resultado_original["taxa_suspeita_real"]
    )


@pytest.mark.parametrize(
    "contamination_invalido",
    [
        0.0,
        0.01,
        0.16,
        np.nan,
        np.inf,
    ],
)
def test_contamination_rejeita_valores_invalidos(
    contamination_invalido,
):
    df = criar_dataset_anomalias()

    with pytest.raises(
        ValueError,
        match="contamination",
    ):
        executar_detectores_anomalia(
            df,
            contamination=contamination_invalido,
        )
