# src/security_detector.py
"""
SecurityDetector - Pipeline de SOC Preditivo (v2)
==================================================
Pipeline principal do SOC Transaction Anomaly Detector.

Responsável por:

• carregar dados do PostgreSQL;
• realizar engenharia de features;
• treinar modelos;
• comparar detectores;
• correlacionar eventos com MITRE ATT&CK;
• gerar métricas e relatório executivo.

"""

import json
import os
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sqlalchemy.engine import Engine

from .alerts.contract import Alert
from .alerts.engine import criar_alerta, deve_gerar_alerta
from .data.repository import SocDataRepository
from .db_connector import DBConnector
from .features.engineering import criar_features
from .models.anomaly_detection import executar_detectores_anomalia
from .models.classification import treinar_classificador_triagem
from .models.evaluation import selecionar_melhor_detector
from .models.regression import treinar_regressao_severidade
from .reporting.charts import (
    gerar_grafico_comparacao,
    gerar_grafico_detector,
    gerar_grafico_importancia_classificador,
)
from .reporting.metrics import salvar_historico_metricas
from .reporting.pdf_report import gerar_relatorio_pdf

# Abaixo deste tamanho de treino, o pipeline continua rodando (é útil para
# desenvolvimento/teste), mas sinaliza explicitamente que as métricas não são
# estatisticamente confiáveis ainda.
MIN_AMOSTRAS_TREINO_CONFIAVEL = 60

# Teto operacional de contamination — 30% de tudo marcado como anômalo não é
# acionável na prática, mesmo que a taxa histórica real diga isso (geralmente
# sinal de dataset de teste com seeds de ataque desproporcionais).
CONTAMINATION_TETO_PRATICO = 0.15


class SecurityDetector:
    def __init__(self, engine: Engine | None = None) -> None:
        if engine is None:
            engine = DBConnector.get_engine()

        self.engine = engine
        self.repository = SocDataRepository(
            engine=self.engine,
            raw_connection_factory=DBConnector.get_raw_connection,
        )
        self.modelo_classificacao = None
        self.modelo_agrupamento = None
        self.modelos_anomalia = {}
        self.melhor_detector = None
        self.modelo_regressao = None
        self.metricas = {}
        self.aviso_amostra_pequena = False
        self.alertas: list[Alert] = []

        os.makedirs("reports", exist_ok=True)
        os.makedirs("reports/models", exist_ok=True)

    # ------------------------------------------------------------------
    # Carga, preparação e auditoria
    # ------------------------------------------------------------------
    def carregar_dados(self) -> pd.DataFrame:
        return self.repository.carregar_dataset_soc()

    # ------------------------------------------------------------------
    # Orquestração
    # ------------------------------------------------------------------
    def analisar_transacoes(self, df_soc: pd.DataFrame) -> pd.DataFrame:
        df = df_soc.copy()
        df["hora"] = pd.to_datetime(df["data_hora_transacao"]).dt.hour

        df = criar_features(df)

        if len(df) < MIN_AMOSTRAS_TREINO_CONFIAVEL:
            self.aviso_amostra_pequena = True
            print(
                f"\n⚠️ ATENÇÃO: apenas {len(df)} transações na base (mínimo recomendado para "
                f"métricas estáveis: {MIN_AMOSTRAS_TREINO_CONFIAVEL}). Os modelos vão treinar "
                f"normalmente, mas trate os resultados como PROVA DE CONCEITO, não como validação "
                f"estatística — isso ficará marcado no relatório."
            )

        df = self._treinar_classificacao(df)
        df = self._comparar_detectores_anomalia(df)
        df = self._treinar_regressao(df)
        self._gerar_alertas(df)
        self._salvar_metricas()
        return df

    def _treinar_classificacao(self, df: pd.DataFrame) -> pd.DataFrame:
        """Executa o classificador supervisionado de triagem do SOC."""
        print(
            "\n⚙️ Treinando classificador de triagem "
            "(features históricas + sinais de log)..."
        )

        resultado = treinar_classificador_triagem(df)

        self.modelo_classificacao = resultado["modelo"]
        self.metricas["classificacao"] = resultado["metricas"]

        metricas = resultado["metricas"]
        classes_no_treino = resultado["classes_no_treino"]
        auc = metricas["roc_auc_teste"]
        cv_scores = resultado["cv_scores"]

        if classes_no_treino < 2:
            self.aviso_amostra_pequena = True
            print(
                "   ⚠️ O treino ficou com apenas 1 classe presente "
                f"({self.modelo_classificacao.classes_[0]}) "
                "— dataset pequeno demais para o classificador aprender "
                "as duas classes ainda."
            )

        print(
            f"   ROC-AUC (teste): {auc:.3f}"
            if not np.isnan(auc)
            else "   ROC-AUC indisponível (classe única no treino ou no teste)"
        )

        if cv_scores:
            print(
                f"   ROC-AUC (CV 3-fold): "
                f"{np.mean(cv_scores):.3f} ± {np.std(cv_scores):.3f}"
            )

        df["proba_suspeita"] = resultado["proba_suspeita"]

        features = resultado["features"]
        importancias = resultado["importancias"]

        gerar_grafico_importancia_classificador(
            features=features,
            importancias=importancias,
            auc=auc,
        )
        joblib.dump(
            self.modelo_classificacao,
            "reports/models/classificador.joblib",
        )

        return df

    def _comparar_detectores_anomalia(self, df: pd.DataFrame) -> pd.DataFrame:
        execucao = executar_detectores_anomalia(df)

        resultados = execucao["resultados"]
        self.modelos_anomalia = execucao["modelos"]

        taxa_suspeita_real = execucao["taxa_suspeita_real"]
        contamination = execucao["contamination"]

        print(f"   taxa histórica suspeita: {taxa_suspeita_real:.3f}")
        print(f"   contamination comum aos modelos: {contamination:.3f}")

        for resultado in resultados:
            nome = resultado["modelo"]

            print(f"\n   ▶ {nome}")

            if resultado["status"] == "erro":
                self.metricas[nome] = resultado
                print(f"      ⚠️ modelo ignorado por erro: {resultado['erro']}")
                continue

            predicoes = execucao["predicoes"][nome]
            predicao_original = predicoes["predicao_original"]
            score_original = predicoes["score_original"]

            df[f"anomalia_{nome}"] = predicao_original
            df[f"score_anomalia_{nome}"] = score_original

            joblib.dump(
                self.modelos_anomalia[nome],
                f"reports/models/{nome}.joblib",
            )

            self.metricas[nome] = resultado

            print(
                f"      anomalias={resultado['qtd_anomalias']} | "
                f"precision={resultado['precision_vs_status_real']:.3f} | "
                f"recall={resultado['recall_vs_status_real']:.3f} | "
                f"F1={resultado['f1_vs_status_real']:.3f} | "
                f"tempo={resultado['tempo_segundos']:.3f}s"
            )

            gerar_grafico_detector(
                df=df,
                nome_modelo=nome,
                contamination=contamination,
            )

        validos = [r for r in resultados if r.get("status") == "ok"]
        melhor = selecionar_melhor_detector(validos)

        self.melhor_detector = melhor["modelo"]
        self.modelo_agrupamento = self.modelos_anomalia[self.melhor_detector]

        # Mantém compatibilidade com o restante do pipeline e com o PDF.
        df["anomalia_score"] = df[f"anomalia_{self.melhor_detector}"]
        df["anomalia_score_bruto"] = df[f"score_anomalia_{self.melhor_detector}"]

        self.metricas["comparacao_detectores"] = {
            "criterio_selecao": "maior F1; desempate por recall, precision e menor tempo",
            "melhor_modelo": self.melhor_detector,
            "resultados": resultados,
        }

        comparacao = pd.DataFrame(validos).sort_values(
            ["f1_vs_status_real", "recall_vs_status_real"], ascending=False
        )
        comparacao.to_csv(
            "reports/comparacao_detectores.csv", index=False, encoding="utf-8-sig"
        )
        with open(
            "reports/comparacao_detectores.json", "w", encoding="utf-8"
        ) as arquivo:
            json.dump(
                self.metricas["comparacao_detectores"],
                arquivo,
                ensure_ascii=False,
                indent=2,
            )

        gerar_grafico_comparacao(comparacao)
        print(f"\n   🏆 Detector selecionado para o relatório: {self.melhor_detector}")
        return df

    def _treinar_regressao(self, df: pd.DataFrame) -> pd.DataFrame:
        print("⚙️ Treinando regressão de severidade de risco...")

        resultado = treinar_regressao_severidade(df)
        metricas = resultado["metricas"]

        self.modelo_regressao = resultado["modelo"]

        self.metricas["regressao"] = {
            "r2_teste": metricas["r2_teste"],
            "mae_teste": metricas["mae_teste"],
            "rmse_teste": metricas["rmse_teste"],
            "r2_cv_media": metricas["r2_cv_media"],
        }

        print(
            f"   R² (teste): {metricas['r2_teste']:.3f} | "
            f"MAE: {metricas['mae_teste']:.1f} | "
            f"RMSE: {metricas['rmse_teste']:.1f}"
        )
        print(
            f"   R² (CV 5-fold): {metricas['r2_cv_media']:.3f} "
            f"± {metricas['r2_cv_desvio']:.3f}"
        )

        if metricas["r2_cv_media"] < 0:
            print(
                "   ⚠️ R² negativo em validação cruzada: o modelo de severidade ainda não "
                "generaliza de forma confiável (típico de base pequena). Isso será sinalizado no PDF."
            )

        df["score_risco_predito"] = resultado["score_risco_predito"]

        joblib.dump(self.modelo_regressao, "reports/models/regressao.joblib")

        return df

    def _gerar_alertas(self, df: pd.DataFrame) -> list[Alert]:
        """Transforma registros analíticos elegíveis em alertas SOC estruturados."""
        if self.melhor_detector is None:
            raise RuntimeError(
                "melhor detector deve ser definido antes da geração de alertas"
            )

        evidencias_observadas = {
            campo
            for campo in (
                "falhas_login_recentes",
                "dispositivo_novo_flag",
                "alteracao_limite_flag",
                "mudanca_localizacao_flag",
            )
            if campo in df.columns
        }

        alertas = []

        for registro in df.to_dict(orient="records"):
            if not deve_gerar_alerta(registro):
                continue

            alerta = criar_alerta(
                registro,
                detector=self.melhor_detector,
                aviso_amostra_pequena=self.aviso_amostra_pequena,
                evidencias_observadas=evidencias_observadas,
            )
            alertas.append(alerta)

        self.alertas = alertas
        return alertas

    def _salvar_metricas(self) -> Path:
        return salvar_historico_metricas(
            metricas=self.metricas,
            aviso_amostra_pequena=self.aviso_amostra_pequena,
        )

    # ------------------------------------------------------------------
    # Relatório PDF
    # ------------------------------------------------------------------
    def gerar_pdf_report(self, df_analisado: pd.DataFrame) -> Path:
        return gerar_relatorio_pdf(
            df_analisado=df_analisado,
            metricas=self.metricas,
            melhor_detector=self.melhor_detector,
            aviso_amostra_pequena=self.aviso_amostra_pequena,
            engine=self.engine,
        )

    def executar_pipeline_completo(self) -> None:
        df_soc = self.carregar_dados()
        df_analisado = self.analisar_transacoes(df_soc)
        self.gerar_pdf_report(df_analisado)
        print("\n🏆 Pipeline do SOC Preditivo Concluído com Sucesso!")


if __name__ == "__main__":
    detector = SecurityDetector()
    detector.executar_pipeline_completo()
