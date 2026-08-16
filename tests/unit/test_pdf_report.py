import numpy as np
import pandas as pd

from src.reporting import pdf_report
from src.reporting.pdf_report import gerar_relatorio_pdf


def criar_metricas():
    return {
        "classificacao": {
            "roc_auc_teste": 0.93,
            "precision_classe_suspeita": 0.90,
            "recall_classe_suspeita": 0.85,
            "n_treino": 100,
            "n_teste": 30,
        },
        "elliptic_envelope": {
            "contamination_usado": 0.15,
            "precision_vs_status_real": 0.95,
            "recall_vs_status_real": 0.80,
            "f1_vs_status_real": 0.87,
        },
        "regressao": {
            "r2_teste": 0.62,
            "mae_teste": 14.5,
            "r2_cv_media": 0.63,
        },
        "comparacao_detectores": {
            "resultados": [
                {
                    "modelo": "isolation_forest",
                    "status": "ok",
                    "qtd_anomalias": 10,
                    "precision_vs_status_real": 0.90,
                    "recall_vs_status_real": 0.70,
                    "f1_vs_status_real": 0.79,
                    "tempo_segundos": 0.20,
                },
                {
                    "modelo": "elliptic_envelope",
                    "status": "ok",
                    "qtd_anomalias": 8,
                    "precision_vs_status_real": 0.95,
                    "recall_vs_status_real": 0.80,
                    "f1_vs_status_real": 0.87,
                    "tempo_segundos": 0.12,
                },
            ]
        },
    }


def criar_dataframe_com_anomalia():
    return pd.DataFrame(
        {
            "id_transacao": [101, 102],
            "cliente_pseudonimo": [
                "cliente-a",
                "cliente-b",
            ],
            "valor_transacao": [
                5000.0,
                100.0,
            ],
            "hora": [
                3,
                14,
            ],
            "anomalia_score": [
                -1,
                1,
            ],
            "score_risco_predito": [
                92.0,
                10.0,
            ],
            "proba_suspeita": [
                0.98,
                0.05,
            ],
            "tipo_transacao": [
                "Pix",
                "Compra",
            ],
            "falhas_login_recentes": [
                3,
                0,
            ],
            "dispositivo_novo_flag": [
                True,
                False,
            ],
            "alteracao_limite_flag": [
                True,
                False,
            ],
            "mudanca_localizacao_flag": [
                False,
                False,
            ],
        }
    )


def test_gerar_relatorio_pdf_cria_arquivo(tmp_path, monkeypatch):
    caminho = tmp_path / "relatorio.pdf"

    monkeypatch.setattr(
        pdf_report,
        "enriquecer_com_mitre",
        lambda **kwargs: {
            "mitre_id": "T1110",
            "tecnica": "Brute Force",
            "tatica": "Credential Access",
            "procedimentos": "Aplicar controles de autenticação.",
            "fonte": "teste",
            "criterio": "falhas de login",
        },
    )

    resultado = gerar_relatorio_pdf(
        df_analisado=criar_dataframe_com_anomalia(),
        metricas=criar_metricas(),
        melhor_detector="elliptic_envelope",
        aviso_amostra_pequena=False,
        engine=object(),
        pdf_path=caminho,
    )

    assert resultado == caminho
    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_relatorio_sem_anomalias_nao_consulta_mitre(
    tmp_path,
    monkeypatch,
):
    caminho = tmp_path / "sem_anomalias.pdf"

    df = criar_dataframe_com_anomalia()
    df["anomalia_score"] = 1

    def mitre_nao_deveria_ser_chamado(**kwargs):
        raise AssertionError("MITRE não deveria ser consultado sem anomalias")

    monkeypatch.setattr(
        pdf_report,
        "enriquecer_com_mitre",
        mitre_nao_deveria_ser_chamado,
    )

    resultado = gerar_relatorio_pdf(
        df_analisado=df,
        metricas=criar_metricas(),
        melhor_detector="elliptic_envelope",
        aviso_amostra_pequena=False,
        engine=object(),
        pdf_path=caminho,
    )

    assert resultado == caminho
    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_relatorio_funciona_sem_id_transacao(
    tmp_path,
    monkeypatch,
):
    caminho = tmp_path / "sem_id.pdf"

    df = criar_dataframe_com_anomalia().drop(columns=["id_transacao"])

    monkeypatch.setattr(
        pdf_report,
        "enriquecer_com_mitre",
        lambda **kwargs: {
            "mitre_id": "T1110",
            "tecnica": "Brute Force",
            "tatica": "Credential Access",
            "procedimentos": "Mitigação simulada.",
            "fonte": "teste",
            "criterio": "correlação simulada",
        },
    )

    resultado = gerar_relatorio_pdf(
        df_analisado=df,
        metricas=criar_metricas(),
        melhor_detector="elliptic_envelope",
        aviso_amostra_pequena=False,
        engine=object(),
        pdf_path=caminho,
    )

    assert resultado == caminho
    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_relatorio_aceita_metricas_indisponiveis(
    tmp_path,
):
    caminho = tmp_path / "metricas_indisponiveis.pdf"

    df = criar_dataframe_com_anomalia()
    df["anomalia_score"] = 1

    metricas = {
        "classificacao": {
            "roc_auc_teste": np.nan,
            "n_treino": 10,
            "n_teste": 5,
        },
        "regressao": {
            "r2_teste": None,
            "mae_teste": None,
            "r2_cv_media": 0.0,
        },
    }

    resultado = gerar_relatorio_pdf(
        df_analisado=df,
        metricas=metricas,
        melhor_detector=None,
        aviso_amostra_pequena=False,
        engine=object(),
        pdf_path=caminho,
    )

    assert resultado == caminho
    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_relatorio_com_aviso_de_amostra_pequena(
    tmp_path,
):
    caminho = tmp_path / "amostra_pequena.pdf"

    df = criar_dataframe_com_anomalia()
    df["anomalia_score"] = 1

    resultado = gerar_relatorio_pdf(
        df_analisado=df,
        metricas=criar_metricas(),
        melhor_detector="elliptic_envelope",
        aviso_amostra_pequena=True,
        engine=object(),
        pdf_path=caminho,
    )

    assert resultado == caminho
    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_relatorio_com_r2_cv_negativo_exibe_fluxo_de_confiabilidade(
    tmp_path,
):
    caminho = tmp_path / "r2_negativo.pdf"

    df = criar_dataframe_com_anomalia()
    df["anomalia_score"] = 1

    metricas = criar_metricas()
    metricas["regressao"]["r2_cv_media"] = -0.25

    resultado = gerar_relatorio_pdf(
        df_analisado=df,
        metricas=metricas,
        melhor_detector="elliptic_envelope",
        aviso_amostra_pequena=False,
        engine=object(),
        pdf_path=caminho,
    )

    assert resultado == caminho
    assert caminho.exists()
    assert caminho.stat().st_size > 0
