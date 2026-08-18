from datetime import UTC, datetime
from pathlib import Path

import pandas as pd
import pytest

from src.security_detector import SecurityDetector


def criar_dataframe_alertas():
    return pd.DataFrame(
        [
            {
                "id_transacao": 1,
                "cliente_pseudonimo": "cliente-01",
                "data_hora_transacao": datetime(
                    2026,
                    8,
                    18,
                    12,
                    0,
                    tzinfo=UTC,
                ),
                "tipo_transacao": "Pix",
                "valor_transacao": 5000.0,
                "proba_suspeita": 0.90,
                "anomalia_score": -1,
                "anomalia_score_bruto": -0.42,
                "score_risco_predito": 92.0,
                "falhas_login_recentes": 4,
                "dispositivo_novo_flag": True,
                "alteracao_limite_flag": True,
                "mudanca_localizacao_flag": False,
            },
            {
                "id_transacao": 2,
                "cliente_pseudonimo": "cliente-02",
                "data_hora_transacao": datetime(
                    2026,
                    8,
                    18,
                    12,
                    30,
                    tzinfo=UTC,
                ),
                "tipo_transacao": "Compra",
                "valor_transacao": 120.0,
                "proba_suspeita": 0.10,
                "anomalia_score": 1,
                "anomalia_score_bruto": 0.31,
                "score_risco_predito": 8.0,
                "falhas_login_recentes": 0,
                "dispositivo_novo_flag": False,
                "alteracao_limite_flag": False,
                "mudanca_localizacao_flag": False,
            },
        ]
    )


def test_gerar_alertas_cria_alerta_apenas_para_registro_elegivel(monkeypatch):
    detector = criar_detector(monkeypatch)
    detector.melhor_detector = "isolation_forest"

    alertas = detector._gerar_alertas(criar_dataframe_alertas())

    assert len(alertas) == 1
    assert len(detector.alertas) == 1

    alerta = alertas[0]

    assert alerta.event.transaction_id == 1
    assert alerta.detection.detector == "isolation_forest"
    assert alerta.detection.anomaly_detected is True
    assert alerta.risk.severity == "critical"


def test_gerar_alertas_retorna_lista_vazia_sem_registros_elegiveis(monkeypatch):
    detector = criar_detector(monkeypatch)
    detector.melhor_detector = "isolation_forest"

    df = criar_dataframe_alertas()

    df["proba_suspeita"] = 0.10
    df["anomalia_score"] = 1

    alertas = detector._gerar_alertas(df)

    assert alertas == []
    assert detector.alertas == []


def test_gerar_alertas_propaga_aviso_amostra_pequena(monkeypatch):
    detector = criar_detector(monkeypatch)
    detector.melhor_detector = "isolation_forest"
    detector.aviso_amostra_pequena = True

    alertas = detector._gerar_alertas(criar_dataframe_alertas())

    assert len(alertas) == 1
    assert alertas[0].quality.small_sample_warning is True


def test_gerar_alertas_preserva_evidencias_observadas(monkeypatch):
    detector = criar_detector(monkeypatch)
    detector.melhor_detector = "isolation_forest"

    df = criar_dataframe_alertas().drop(
        columns=[
            "alteracao_limite_flag",
            "mudanca_localizacao_flag",
        ]
    )

    alertas = detector._gerar_alertas(df)

    alerta = alertas[0]

    assert alerta.evidence.failed_logins.observed is True
    assert alerta.evidence.new_device.observed is True
    assert alerta.evidence.limit_change.observed is False
    assert alerta.evidence.location_change.observed is False

    assert alerta.quality.missing_evidence == (
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    )


def test_gerar_alertas_exige_melhor_detector(monkeypatch):
    detector = criar_detector(monkeypatch)

    with pytest.raises(
        RuntimeError,
        match="melhor detector deve ser definido",
    ):
        detector._gerar_alertas(criar_dataframe_alertas())


def criar_detector(monkeypatch):
    """Cria SecurityDetector sem produzir diretórios durante o teste."""
    monkeypatch.setattr(
        "src.security_detector.os.makedirs",
        lambda *args, **kwargs: None,
    )

    return SecurityDetector(engine=object())


def test_carregar_dados_delega_para_repository(monkeypatch):
    detector = criar_detector(monkeypatch)

    esperado = pd.DataFrame(
        {
            "id_transacao": [1, 2],
            "valor_transacao": [100.0, 200.0],
        }
    )

    chamadas = []

    def fake_carregar_dataset_soc():
        chamadas.append("repository")
        return esperado

    monkeypatch.setattr(
        detector.repository,
        "carregar_dataset_soc",
        fake_carregar_dataset_soc,
    )

    resultado = detector.carregar_dados()

    assert chamadas == ["repository"]
    assert resultado is esperado


def test_analisar_transacoes_executa_etapas_na_ordem(monkeypatch):
    detector = criar_detector(monkeypatch)

    df_original = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-15 08:00:00",
                "2026-08-15 09:00:00",
            ]
        }
    )

    chamadas = []

    def fake_criar_features(df):
        chamadas.append("features")
        resultado = df.copy()
        resultado["feature_fake"] = 1
        return resultado

    def fake_classificacao(df):
        chamadas.append("classificacao")
        assert "feature_fake" in df.columns

        resultado = df.copy()
        resultado["classificacao_fake"] = 1
        return resultado

    def fake_anomalia(df):
        chamadas.append("anomalia")
        assert "classificacao_fake" in df.columns

        resultado = df.copy()
        resultado["anomalia_fake"] = 1
        return resultado

    def fake_regressao(df):
        chamadas.append("regressao")
        assert "anomalia_fake" in df.columns

        resultado = df.copy()
        resultado["regressao_fake"] = 1
        return resultado

    def fake_salvar_metricas():
        chamadas.append("metricas")
        return Path("fake.jsonl")

    def fake_gerar_alertas(df):
        chamadas.append("alertas")
        assert "regressao_fake" in df.columns
        return []

    monkeypatch.setattr(
        "src.security_detector.criar_features",
        fake_criar_features,
    )
    monkeypatch.setattr(
        detector,
        "_treinar_classificacao",
        fake_classificacao,
    )
    monkeypatch.setattr(
        detector,
        "_comparar_detectores_anomalia",
        fake_anomalia,
    )
    monkeypatch.setattr(
        detector,
        "_treinar_regressao",
        fake_regressao,
    )
    monkeypatch.setattr(
        detector,
        "_salvar_metricas",
        fake_salvar_metricas,
    )

    monkeypatch.setattr(
        detector,
        "_gerar_alertas",
        fake_gerar_alertas,
    )

    resultado = detector.analisar_transacoes(df_original)

    assert chamadas == [
        "features",
        "classificacao",
        "anomalia",
        "regressao",
        "alertas",
        "metricas",
    ]

    assert "feature_fake" in resultado.columns
    assert "classificacao_fake" in resultado.columns
    assert "anomalia_fake" in resultado.columns
    assert "regressao_fake" in resultado.columns


def test_analisar_transacoes_cria_coluna_hora(monkeypatch):
    detector = criar_detector(monkeypatch)

    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-15 03:30:00",
                "2026-08-15 18:45:00",
            ]
        }
    )

    monkeypatch.setattr(
        "src.security_detector.criar_features",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        detector,
        "_treinar_classificacao",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        detector,
        "_comparar_detectores_anomalia",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        detector,
        "_treinar_regressao",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        detector,
        "_gerar_alertas",
        lambda _: [],
    )
    monkeypatch.setattr(
        detector,
        "_salvar_metricas",
        lambda: Path("fake.jsonl"),
    )

    resultado = detector.analisar_transacoes(df)

    assert resultado["hora"].tolist() == [3, 18]


def test_dataset_pequeno_ativa_aviso(monkeypatch):
    detector = criar_detector(monkeypatch)

    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-15 10:00:00",
                "2026-08-15 11:00:00",
            ]
        }
    )

    monkeypatch.setattr(
        "src.security_detector.criar_features",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        detector,
        "_treinar_classificacao",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        detector,
        "_comparar_detectores_anomalia",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        detector,
        "_treinar_regressao",
        lambda dataframe: dataframe,
    )
    monkeypatch.setattr(
        detector,
        "_gerar_alertas",
        lambda _: [],
    )
    monkeypatch.setattr(
        detector,
        "_salvar_metricas",
        lambda: Path("fake.jsonl"),
    )

    detector.analisar_transacoes(df)

    assert detector.aviso_amostra_pequena is True


def test_salvar_metricas_delega_para_modulo_reporting(monkeypatch):
    detector = criar_detector(monkeypatch)

    detector.metricas = {
        "classificacao": {
            "roc_auc_teste": 0.993,
        }
    }
    detector.aviso_amostra_pequena = True

    caminho_esperado = Path("reports/fake_metricas.jsonl")
    argumentos = {}

    def fake_salvar_historico_metricas(
        metricas,
        aviso_amostra_pequena,
    ):
        argumentos["metricas"] = metricas
        argumentos["aviso"] = aviso_amostra_pequena
        return caminho_esperado

    monkeypatch.setattr(
        "src.security_detector.salvar_historico_metricas",
        fake_salvar_historico_metricas,
    )

    resultado = detector._salvar_metricas()

    assert resultado == caminho_esperado
    assert argumentos["metricas"] == detector.metricas
    assert argumentos["aviso"] is True


def test_gerar_pdf_report_delega_para_reporting(monkeypatch):
    detector = criar_detector(monkeypatch)

    detector.metricas = {"teste": 123}
    detector.melhor_detector = "elliptic_envelope"
    detector.aviso_amostra_pequena = False

    df = pd.DataFrame(
        {
            "id_transacao": [1],
        }
    )

    caminho_esperado = Path("reports/fake.pdf")
    argumentos = {}

    def fake_gerar_relatorio_pdf(**kwargs):
        argumentos.update(kwargs)
        return caminho_esperado

    monkeypatch.setattr(
        "src.security_detector.gerar_relatorio_pdf",
        fake_gerar_relatorio_pdf,
    )

    resultado = detector.gerar_pdf_report(df)

    assert resultado == caminho_esperado
    assert argumentos["df_analisado"] is df
    assert argumentos["metricas"] == detector.metricas
    assert argumentos["melhor_detector"] == "elliptic_envelope"
    assert argumentos["aviso_amostra_pequena"] is False
    assert argumentos["engine"] is detector.engine


def test_executar_pipeline_completo_orquestra_fluxo(monkeypatch):
    detector = criar_detector(monkeypatch)

    df_carregado = pd.DataFrame(
        {
            "etapa": ["carregado"],
        }
    )

    df_analisado = pd.DataFrame(
        {
            "etapa": ["analisado"],
        }
    )

    chamadas = []

    def fake_carregar_dados():
        chamadas.append("carregar")
        return df_carregado

    def fake_analisar_transacoes(df):
        chamadas.append("analisar")
        assert df is df_carregado
        return df_analisado

    def fake_gerar_pdf_report(df):
        chamadas.append("pdf")
        assert df is df_analisado
        return Path("reports/fake.pdf")

    monkeypatch.setattr(
        detector,
        "carregar_dados",
        fake_carregar_dados,
    )
    monkeypatch.setattr(
        detector,
        "analisar_transacoes",
        fake_analisar_transacoes,
    )
    monkeypatch.setattr(
        detector,
        "gerar_pdf_report",
        fake_gerar_pdf_report,
    )

    resultado = detector.executar_pipeline_completo()

    assert resultado is None
    assert chamadas == [
        "carregar",
        "analisar",
        "pdf",
    ]


def test_treinar_classificacao_integra_resultado_no_detector(monkeypatch):
    detector = criar_detector(monkeypatch)

    df = pd.DataFrame({"valor": [1, 2]})

    modelo_fake = object()

    resultado_fake = {
        "modelo": modelo_fake,
        "metricas": {
            "roc_auc_teste": 0.91,
            "roc_auc_cv_media": 0.90,
        },
        "classes_no_treino": 2,
        "cv_scores": [0.89, 0.90, 0.91],
        "proba_suspeita": [0.1, 0.8],
        "features": ["hora", "valor"],
        "importancias": [0.4, 0.6],
    }

    monkeypatch.setattr(
        "src.security_detector.treinar_classificador_triagem",
        lambda dataframe: resultado_fake,
    )

    grafico = {}

    def fake_grafico(**kwargs):
        grafico.update(kwargs)

    monkeypatch.setattr(
        "src.security_detector.gerar_grafico_importancia_classificador",
        fake_grafico,
    )

    dumps = []

    monkeypatch.setattr(
        "src.security_detector.joblib.dump",
        lambda modelo, caminho: dumps.append((modelo, caminho)),
    )

    resultado = detector._treinar_classificacao(df)

    assert detector.modelo_classificacao is modelo_fake
    assert detector.metricas["classificacao"] == resultado_fake["metricas"]
    assert resultado["proba_suspeita"].tolist() == [0.1, 0.8]

    assert grafico["features"] == ["hora", "valor"]
    assert grafico["importancias"] == [0.4, 0.6]
    assert grafico["auc"] == 0.91
    assert dumps == [
        (
            modelo_fake,
            "reports/models/classificador.joblib",
        )
    ]


def test_treinar_classificacao_classe_unica_ativa_aviso(monkeypatch):
    detector = criar_detector(monkeypatch)

    class ModeloFake:
        classes_ = [0]

    resultado_fake = {
        "modelo": ModeloFake(),
        "metricas": {
            "roc_auc_teste": float("nan"),
            "roc_auc_cv_media": None,
        },
        "classes_no_treino": 1,
        "cv_scores": [],
        "proba_suspeita": [0.0, 0.0],
        "features": ["hora"],
        "importancias": [1.0],
    }

    monkeypatch.setattr(
        "src.security_detector.treinar_classificador_triagem",
        lambda dataframe: resultado_fake,
    )

    monkeypatch.setattr(
        "src.security_detector.gerar_grafico_importancia_classificador",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        "src.security_detector.joblib.dump",
        lambda *args, **kwargs: None,
    )

    df = pd.DataFrame({"valor": [1, 2]})

    detector._treinar_classificacao(df)

    assert detector.aviso_amostra_pequena is True


def test_treinar_regressao_integra_resultado_no_detector(monkeypatch):
    detector = criar_detector(monkeypatch)

    modelo_fake = object()

    resultado_fake = {
        "modelo": modelo_fake,
        "score_risco_predito": [20.0, 80.0],
        "metricas": {
            "r2_teste": 0.75,
            "mae_teste": 10.0,
            "rmse_teste": 15.0,
            "r2_cv_media": 0.70,
            "r2_cv_desvio": 0.05,
        },
    }

    monkeypatch.setattr(
        "src.security_detector.treinar_regressao_severidade",
        lambda dataframe: resultado_fake,
    )

    dumps = []

    monkeypatch.setattr(
        "src.security_detector.joblib.dump",
        lambda modelo, caminho: dumps.append((modelo, caminho)),
    )

    df = pd.DataFrame({"valor": [1, 2]})

    resultado = detector._treinar_regressao(df)

    assert detector.modelo_regressao is modelo_fake

    assert detector.metricas["regressao"] == {
        "r2_teste": 0.75,
        "mae_teste": 10.0,
        "rmse_teste": 15.0,
        "r2_cv_media": 0.70,
    }

    assert resultado["score_risco_predito"].tolist() == [20.0, 80.0]

    assert dumps == [
        (
            modelo_fake,
            "reports/models/regressao.joblib",
        )
    ]


def test_regressao_cv_negativo_emite_aviso(monkeypatch, capsys):
    detector = criar_detector(monkeypatch)

    resultado_fake = {
        "modelo": object(),
        "score_risco_predito": [30.0],
        "metricas": {
            "r2_teste": -0.2,
            "mae_teste": 20.0,
            "rmse_teste": 25.0,
            "r2_cv_media": -0.3,
            "r2_cv_desvio": 0.1,
        },
    }

    monkeypatch.setattr(
        "src.security_detector.treinar_regressao_severidade",
        lambda dataframe: resultado_fake,
    )

    monkeypatch.setattr(
        "src.security_detector.joblib.dump",
        lambda *args, **kwargs: None,
    )

    detector._treinar_regressao(pd.DataFrame({"valor": [1]}))

    saida = capsys.readouterr()

    assert "R² negativo" in saida.out


def test_comparar_detectores_integra_execucao_e_escolhe_vencedor(
    monkeypatch,
    tmp_path,
):
    detector = criar_detector(monkeypatch)

    modelo_a = object()
    modelo_b = object()

    execucao_fake = {
        "taxa_suspeita_real": 0.2,
        "contamination": 0.15,
        "modelos": {
            "modelo_a": modelo_a,
            "modelo_b": modelo_b,
        },
        "predicoes": {
            "modelo_a": {
                "predicao_original": [1, -1],
                "score_original": [0.8, -0.5],
            },
            "modelo_b": {
                "predicao_original": [-1, -1],
                "score_original": [-0.4, -0.8],
            },
        },
        "resultados": [
            {
                "modelo": "modelo_a",
                "status": "ok",
                "qtd_anomalias": 1,
                "precision_vs_status_real": 0.8,
                "recall_vs_status_real": 0.7,
                "f1_vs_status_real": 0.75,
                "tempo_segundos": 0.1,
            },
            {
                "modelo": "modelo_b",
                "status": "ok",
                "qtd_anomalias": 2,
                "precision_vs_status_real": 0.9,
                "recall_vs_status_real": 0.8,
                "f1_vs_status_real": 0.85,
                "tempo_segundos": 0.2,
            },
        ],
    }

    monkeypatch.setattr(
        "src.security_detector.executar_detectores_anomalia",
        lambda dataframe: execucao_fake,
    )

    monkeypatch.setattr(
        "src.security_detector.selecionar_melhor_detector",
        lambda resultados: resultados[1],
    )

    monkeypatch.setattr(
        "src.security_detector.joblib.dump",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        "src.security_detector.gerar_grafico_detector",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        "src.security_detector.gerar_grafico_comparacao",
        lambda comparacao: None,
    )

    monkeypatch.chdir(tmp_path)

    (tmp_path / "reports").mkdir()

    df = pd.DataFrame(
        {
            "valor_transacao": [100, 200],
        }
    )

    resultado = detector._comparar_detectores_anomalia(df)

    assert detector.melhor_detector == "modelo_b"
    assert detector.modelo_agrupamento is modelo_b

    assert resultado["anomalia_score"].tolist() == [-1, -1]
    assert resultado["anomalia_score_bruto"].tolist() == [-0.4, -0.8]

    assert detector.metricas["comparacao_detectores"]["melhor_modelo"] == "modelo_b"


def test_init_cria_engine_quando_nao_injetada(monkeypatch):
    engine_fake = object()

    monkeypatch.setattr(
        "src.security_detector.DBConnector.get_engine",
        lambda: engine_fake,
    )

    monkeypatch.setattr(
        "src.security_detector.os.makedirs",
        lambda *args, **kwargs: None,
    )

    detector = SecurityDetector()

    assert detector.engine is engine_fake


def test_comparar_detectores_registra_modelo_com_erro(monkeypatch):
    detector = criar_detector(monkeypatch)

    modelo_ok = object()

    execucao_fake = {
        "taxa_suspeita_real": 0.2,
        "contamination": 0.15,
        "modelos": {
            "modelo_ok": modelo_ok,
        },
        "predicoes": {
            "modelo_ok": {
                "predicao_original": [1, -1],
                "score_original": [0.5, -0.4],
            }
        },
        "resultados": [
            {
                "modelo": "modelo_erro",
                "status": "erro",
                "erro": "falha simulada",
                "tempo_segundos": 0.01,
            },
            {
                "modelo": "modelo_ok",
                "status": "ok",
                "qtd_anomalias": 1,
                "precision_vs_status_real": 1.0,
                "recall_vs_status_real": 1.0,
                "f1_vs_status_real": 1.0,
                "tempo_segundos": 0.02,
            },
        ],
    }

    monkeypatch.setattr(
        "src.security_detector.executar_detectores_anomalia",
        lambda dataframe: execucao_fake,
    )

    monkeypatch.setattr(
        "src.security_detector.selecionar_melhor_detector",
        lambda resultados: resultados[0],
    )

    monkeypatch.setattr(
        "src.security_detector.joblib.dump",
        lambda *args, **kwargs: None,
    )

    monkeypatch.setattr(
        "src.security_detector.gerar_grafico_detector",
        lambda **kwargs: None,
    )

    monkeypatch.setattr(
        "src.security_detector.gerar_grafico_comparacao",
        lambda comparacao: None,
    )

    df = pd.DataFrame(
        {
            "valor_transacao": [100, 200],
        }
    )

    detector._comparar_detectores_anomalia(df)

    assert detector.metricas["modelo_erro"]["status"] == "erro"
    assert detector.metricas["modelo_erro"]["erro"] == "falha simulada"
    assert detector.melhor_detector == "modelo_ok"
