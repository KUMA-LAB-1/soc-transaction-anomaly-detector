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

import getpass
import html
import json
import os
import re
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from sqlalchemy import text

from .data.columns import resolver_coluna_cliente
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

# Abaixo deste tamanho de treino, o pipeline continua rodando (é útil para
# desenvolvimento/teste), mas sinaliza explicitamente que as métricas não são
# estatisticamente confiáveis ainda.
MIN_AMOSTRAS_TREINO_CONFIAVEL = 60

# Teto operacional de contamination — 30% de tudo marcado como anômalo não é
# acionável na prática, mesmo que a taxa histórica real diga isso (geralmente
# sinal de dataset de teste com seeds de ataque desproporcionais).
CONTAMINATION_TETO_PRATICO = 0.15


class SecurityDetector:
    def __init__(self, engine=None):
        if engine is None:
            engine = DBConnector.get_engine()

        self.engine = engine
        self.modelo_classificacao = None
        self.modelo_agrupamento = None
        self.modelos_anomalia = {}
        self.melhor_detector = None
        self.modelo_regressao = None
        self.metricas = {}
        self.aviso_amostra_pequena = False

        os.makedirs("reports", exist_ok=True)
        os.makedirs("reports/models", exist_ok=True)

    # ------------------------------------------------------------------
    # Carga, preparação e auditoria
    # ------------------------------------------------------------------
    def validar_e_preparar_dataset(self, df, nome_tabela):
        if df.isnull().sum().sum() > 0:
            df = df.fillna(0)
        return df.drop_duplicates()

    def _registrar_auditoria(self, view_acessada, qtd_linhas, finalidade):
        """[ITEM 10] Log de accountability: quem acessou dados sensíveis, quando, quantos."""
        try:
            usuario = (
                os.getenv("SOC_PIPELINE_USER")
                or getpass.getuser()
                or "pipeline_automatizado"
            )
            conn = DBConnector.get_raw_connection()
            cur = conn.cursor()
            cur.execute(
                "INSERT INTO tbl_auditoria_acessos "
                "(usuario_execucao, view_ou_tabela_acessada, qtd_linhas_retornadas, finalidade) "
                "VALUES (%s, %s, %s, %s)",
                (usuario, view_acessada, int(qtd_linhas), finalidade),
            )
            conn.commit()
            cur.close()
            conn.close()
        except Exception as e:
            print(
                f"⚠️ Não foi possível registrar auditoria de acesso (tabela existe? rode 08_hardening_e_correlacao.sql): {e}"
            )

    def carregar_dados(self):
        try:
            query_view = "SELECT * FROM v_analise_investigacao_soc;"
            df_consolidado = pd.read_sql_query(query_view, self.engine)
            df_consolidado = self.validar_e_preparar_dataset(
                df_consolidado, "v_analise_investigacao_soc"
            )
            self._registrar_auditoria(
                "v_analise_investigacao_soc",
                len(df_consolidado),
                "Execução do pipeline de detecção preditiva do SOC",
            )
            return df_consolidado
        except Exception as e:
            print(f"❌ Erro na leitura segura do banco: {e}")
            raise

    # ------------------------------------------------------------------
    # Orquestração
    # ------------------------------------------------------------------
    def processar_modelos_e_graficos(self, df_soc):
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
        self._salvar_metricas()
        return df

    def _treinar_classificacao(self, df):
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

        return df

    def _comparar_detectores_anomalia(self, df):

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

    def _treinar_regressao(self, df):
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

    def _salvar_metricas(self):
        registro = {
            "timestamp": datetime.utcnow().isoformat(),
            "amostra_pequena": self.aviso_amostra_pequena,
            **self.metricas,
        }
        caminho = Path("reports/historico_metricas.jsonl")
        with open(caminho, "a", encoding="utf-8") as f:
            f.write(json.dumps(registro, ensure_ascii=False, default=str) + "\n")
        print(f"📈 Métricas registradas em {caminho}")

    # ------------------------------------------------------------------
    # Threat hunting MITRE [ITEM 6]
    # ------------------------------------------------------------------
    def _determinar_padrao_por_correlacao(self, sinais):
        """
        Decide a técnica MITRE a partir de sinais REAIS de comportamento
        (correlação com tbl_logs_seguranca), não do texto do tipo de transação.
        Retorna (termo_busca, descricao_criterio) ou (None, None) se nenhum
        sinal de log bateu — nesse caso cai no fallback por tipo de transação.
        """
        if sinais.get("falhas_login_recentes", 0) >= 2:
            return (
                "%T1110%",
                "múltiplas falhas de login antes da transação (força bruta)",
            )
        if sinais.get("dispositivo_novo_flag") and sinais.get("alteracao_limite_flag"):
            return (
                "%T1098%",
                "dispositivo novo vinculado + alteração de limite Pix (tomada de conta)",
            )
        if sinais.get("mudanca_localizacao_flag"):
            return (
                "%T1078%",
                "mudança de localização entre acessos recentes (uso de credencial fora do padrão)",
            )
        return None, None

    @staticmethod
    def _limpar_texto_mitre(texto):
        """[ITEM 9] Remove links markdown/citações do texto bruto do MITRE e escapa
        caracteres especiais antes de ir para o Paragraph do reportlab."""
        if not texto:
            return "Nenhum procedimento de mitigação listado."
        texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)  # [Nome](url) -> Nome
        texto = re.sub(r"\(Citation:[^)]*\)", "", texto)  # remove (Citation: ...)
        texto = re.sub(r"\s+", " ", texto).strip()
        if len(texto) > 450:
            texto = texto[:450].rsplit(" ", 1)[0] + "…"
        return html.escape(texto)

    def enriquecer_com_mitre(self, tipo_evento, sinais=None):
        sinais = sinais or {}
        termo_busca, criterio = self._determinar_padrao_por_correlacao(sinais)
        if not termo_busca:
            criterio = "tipo de transação (fallback, sem correlação de log disponível)"
            if "Pix" in tipo_evento:
                termo_busca = "%T1565%"
            elif "Transferência" in tipo_evento:
                termo_busca = "%T1043%"
            else:
                termo_busca = "%T1110%"

        try:
            query = text("""
                SELECT mitre_id, mitre_tecnica, mitre_tatica, procedimentos
                FROM tbl_mitre_mapping
                WHERE mitre_id ILIKE :termo OR mitre_tecnica ILIKE :termo
                ORDER BY mitre_id
                LIMIT 1;
            """)
            with self.engine.connect() as conn:
                result = conn.execute(query, {"termo": termo_busca}).fetchone()
                if result:
                    return {
                        "mitre_id": html.escape(str(result[0])),
                        "tecnica": html.escape(str(result[1])),
                        "tatica": html.escape(str(result[2])),
                        "procedimentos": self._limpar_texto_mitre(result[3]),
                        "fonte": "banco de dados (dinâmico)",
                        "criterio": criterio,
                    }
        except Exception as e:
            print(
                f"⚠️ Alerta ao consultar Threat Intel no banco: {e}. Usando mapeamento local resiliente."
            )

        if "Pix" in tipo_evento:
            return {
                "mitre_id": "T1565.001",
                "tecnica": "Manipulação de Dados: Transferência Financeira Não Autorizada",
                "tatica": "Impacto / Roubo de Ativos",
                "procedimentos": "Aplicar MFA mandatório para transações fora do horário comercial.",
                "fonte": "fallback local",
                "criterio": criterio,
            }
        return {
            "mitre_id": "T1110.001",
            "tecnica": "Ataque de Força Bruta (Brute Force Credential Stuffing)",
            "tatica": "Acesso Inicial",
            "procedimentos": "Bloquear temporariamente o IP de origem e forçar redefinição de senha.",
            "fonte": "fallback local",
            "criterio": criterio,
        }

    # ------------------------------------------------------------------
    # Relatório PDF
    # ------------------------------------------------------------------
    def gerar_pdf_report(self, df_analisado):
        pdf_path = "reports/Relatorio_Incidente_SOC.pdf"
        print(f"\n📄 Compilando Relatório Executivo PDF em '{pdf_path}'...")

        col_cliente = resolver_coluna_cliente(df_analisado)
        col_id_transacao = (
            "id_transacao" if "id_transacao" in df_analisado.columns else None
        )

        doc = SimpleDocTemplate(
            pdf_path,
            pagesize=letter,
            rightMargin=40,
            leftMargin=40,
            topMargin=40,
            bottomMargin=40,
        )
        styles = getSampleStyleSheet()
        titulo_style = ParagraphStyle(
            "TituloSOC",
            parent=styles["Heading1"],
            fontSize=20,
            leading=24,
            textColor=colors.HexColor("#0f2b5c"),
            spaceAfter=15,
        )
        sub_style = ParagraphStyle(
            "SubSOC",
            parent=styles["Normal"],
            fontSize=10,
            textColor=colors.HexColor("#555555"),
            spaceAfter=25,
        )
        corpo_style = ParagraphStyle(
            "CorpoSOC",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#333333"),
            spaceAfter=12,
        )
        aviso_style = ParagraphStyle(
            "AvisoSOC",
            parent=styles["Normal"],
            fontSize=10,
            leading=14,
            textColor=colors.HexColor("#8a2b00"),
            spaceAfter=12,
            backColor=colors.HexColor("#fff3e0"),
        )

        elementos = [
            Paragraph(
                "RELATÓRIO DE DETECÇÃO DE INCIDENTES - SOC PREDITIVO", titulo_style
            ),
            Paragraph(
                "Análise de ML, validação de modelos e mapeamento MITRE ATT&CK",
                sub_style,
            ),
        ]

        m_reg_preview = self.metricas.get("regressao", {})
        if self.aviso_amostra_pequena or (m_reg_preview.get("r2_cv_media", 0) or 0) < 0:
            texto_aviso = (
                "⚠️ AVISO DE CONFIABILIDADE: a base analisada é pequena e/ou os modelos ainda não "
                "generalizam de forma estável (ver métricas na seção 4). Trate os números deste "
                "relatório como PROVA DE CONCEITO, não como validação estatística definitiva. "
                "Recomenda-se aumentar o volume de transações reais/rotuladas antes de usar estes "
                "scores operacionalmente."
            )
            elementos.append(Paragraph(texto_aviso, aviso_style))
            elementos.append(Spacer(1, 10))

        elementos.append(Paragraph("<b>1. Resumo Executivo</b>", styles["Heading2"]))

        anomalias = df_analisado[df_analisado["anomalia_score"] == -1]
        qtd_anomalias = len(anomalias)
        m_clf = self.metricas.get("classificacao", {})
        m_detector = self.metricas.get(self.melhor_detector or "isolation_forest", {})
        m_reg = self.metricas.get("regressao", {})

        auc_txt = (
            f"{m_clf.get('roc_auc_teste'):.2f}"
            if m_clf.get("roc_auc_teste") is not None
            and not np.isnan(m_clf.get("roc_auc_teste", float("nan")))
            else "N/D"
        )
        r2_txt = (
            f"{m_reg.get('r2_teste'):.2f}"
            if m_reg.get("r2_teste") is not None
            else "N/D"
        )
        mae_txt = (
            f"{m_reg.get('mae_teste'):.1f}"
            if m_reg.get("mae_teste") is not None
            else "N/D"
        )

        texto_resumo = (
            f"Este relatório documenta {qtd_anomalias} transações sinalizadas por detecção de anomalias "
            f"({(self.melhor_detector or 'isolation_forest').replace('_', ' ').title()}, contamination={m_detector.get('contamination_usado', 0):.2f}). "
            f"O classificador de triagem atingiu ROC-AUC de {auc_txt} em dados de teste. "
            f"O modelo de severidade (regressão) obteve R²={r2_txt} e erro médio absoluto "
            f"de {mae_txt} pontos em uma escala de 0-100."
        )
        elementos.append(Paragraph(texto_resumo, corpo_style))
        elementos.append(Spacer(1, 10))

        elementos.append(
            Paragraph(
                "<b>2. Detalhes Técnicos dos Alertas de Alta Severidade</b>",
                styles["Heading2"],
            )
        )
        tabela_dados = [
            [
                "Ref/ID",
                "Cliente (LGPD)",
                "Valor",
                "Horário",
                "Score Predito",
                "Prob. Suspeita",
            ]
        ]
        for i, (idx, row) in enumerate(anomalias.iterrows(), start=1):
            id_referencia = (
                str(row[col_id_transacao]) if col_id_transacao else f"INC-{i:03d}"
            )
            tabela_dados.append(
                [
                    id_referencia,
                    str(row[col_cliente]),
                    f"R$ {float(row['valor_transacao']):,.2f}",
                    f"{int(row['hora'])}:00h",
                    f"{row['score_risco_predito']:.1f}/100",
                    f"{row.get('proba_suspeita', 0):.0%}",
                ]
            )
        t_incidentes = Table(tabela_dados, colWidths=[55, 100, 90, 60, 80, 80])
        t_incidentes.setStyle(
            TableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2b5c")),
                    ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                    ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                    ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                    ("FONTSIZE", (0, 0), (-1, 0), 10),
                    ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
                    ("BACKGROUND", (0, 1), (-1, -1), colors.HexColor("#f7f9fc")),
                    ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e0e0e0")),
                    ("FONTSIZE", (0, 1), (-1, -1), 9),
                ]
            )
        )
        elementos.append(t_incidentes)
        elementos.append(Spacer(1, 25))

        elementos.append(
            Paragraph(
                "<b>3. Correlação de Threat Intelligence (MITRE ATT&CK)</b>",
                styles["Heading2"],
            )
        )
        if qtd_anomalias == 0:
            elementos.append(
                Paragraph(
                    "Nenhuma anomalia crítica correlacionada com táticas MITRE.",
                    corpo_style,
                )
            )
        else:
            ameacas_vistas = set()
            for _, row in anomalias.iterrows():
                tipo_evento = row.get("tipo_transacao", "Pix")
                sinais = {
                    "falhas_login_recentes": row.get("falhas_login_recentes", 0),
                    "dispositivo_novo_flag": row.get("dispositivo_novo_flag", False),
                    "alteracao_limite_flag": row.get("alteracao_limite_flag", False),
                    "mudanca_localizacao_flag": row.get(
                        "mudanca_localizacao_flag", False
                    ),
                }
                intel = self.enriquecer_com_mitre(tipo_evento, sinais)
                chave = (intel["mitre_id"], row[col_cliente])
                if intel and chave not in ameacas_vistas:
                    ameacas_vistas.add(chave)
                    texto_dinamico_mitre = (
                        f"<b>Técnica associada:</b> {intel['tecnica']} (ID: <b>{intel['mitre_id']}</b>), "
                        f"tática <b>{intel['tatica']}</b>. Fonte: {intel['fonte']}.<br/>"
                        f"• <b>Critério de correlação:</b> {html.escape(intel['criterio'])}.<br/>"
                        f"• <b>Cliente (pseudônimo):</b> {row[col_cliente]} às {int(row['hora'])}:00h.<br/>"
                        f"• <b>Procedimentos sugeridos:</b> {intel['procedimentos']}"
                    )
                    elementos.append(Paragraph(texto_dinamico_mitre, corpo_style))
                    elementos.append(Spacer(1, 10))

        elementos.append(
            Paragraph(
                "<b>4. Validação dos Modelos (transparência metodológica)</b>",
                styles["Heading2"],
            )
        )
        precision_clf = m_clf.get("precision_classe_suspeita") or 0
        recall_clf = m_clf.get("recall_classe_suspeita") or 0
        precision_detector = m_detector.get("precision_vs_status_real") or 0
        recall_detector = m_detector.get("recall_vs_status_real") or 0
        f1_detector = m_detector.get("f1_vs_status_real") or 0
        r2_cv = m_reg.get("r2_cv_media") or 0
        n_treino = m_clf.get("n_treino", 0)
        n_teste = m_clf.get("n_teste", 0)
        texto_validacao = (
            f"Amostra: {n_treino} transações de treino / {n_teste} de teste. "
            f"Classificador de triagem: precision={precision_clf:.2f}, recall={recall_clf:.2f} "
            f"(reproduz decisões históricas, não detecta ataques inéditos). "
            f"Detector selecionado ({(self.melhor_detector or 'N/D').replace('_', ' ')}): "
            f"precision={precision_detector:.2f}, recall={recall_detector:.2f}, F1={f1_detector:.2f} "
            f"(rótulo usado somente para auditoria comparativa). "
            f"Regressão de severidade: R² (validação cruzada 5-fold)={r2_cv:.2f}."
        )
        elementos.append(Paragraph(texto_validacao, corpo_style))

        comparacao_info = self.metricas.get("comparacao_detectores", {}).get(
            "resultados", []
        )
        comparacao_validos = [r for r in comparacao_info if r.get("status") == "ok"]
        if comparacao_validos:
            elementos.append(Spacer(1, 14))
            elementos.append(
                Paragraph(
                    "<b>5. Comparação dos Detectores de Anomalia</b>",
                    styles["Heading2"],
                )
            )
            tabela_modelos = [
                ["Modelo", "Alertas", "Precision", "Recall", "F1", "Tempo (s)"]
            ]
            for r in sorted(
                comparacao_validos, key=lambda x: x["f1_vs_status_real"], reverse=True
            ):
                tabela_modelos.append(
                    [
                        r["modelo"].replace("_", " "),
                        str(r["qtd_anomalias"]),
                        f"{r['precision_vs_status_real']:.2f}",
                        f"{r['recall_vs_status_real']:.2f}",
                        f"{r['f1_vs_status_real']:.2f}",
                        f"{r['tempo_segundos']:.3f}",
                    ]
                )
            t_modelos = Table(tabela_modelos, colWidths=[120, 55, 60, 55, 45, 65])
            t_modelos.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f2b5c")),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("GRID", (0, 0), (-1, -1), 1, colors.HexColor("#e0e0e0")),
                        ("FONTSIZE", (0, 0), (-1, -1), 8),
                    ]
                )
            )
            elementos.append(t_modelos)
            elementos.append(Spacer(1, 8))
            elementos.append(
                Paragraph(
                    "O detector selecionado representa o melhor desempenho obtido entre os modelos avaliados "
                    "neste conjunto de dados, considerando F1-score, recall, precision e tempo de execução. "
                    "Como a avaliação foi realizada sobre uma base sintética, os resultados demonstram a "
                    "viabilidade da abordagem proposta e podem servir como referência para estudos futuros "
                    "utilizando dados reais.",
                )
            )

        doc.build(elementos)
        print(f"🚀 [SUCESSO] Relatório PDF '{pdf_path}' gerado.")

    def executar_pipeline_completo(self):
        df_soc = self.carregar_dados()
        df_analisado = self.processar_modelos_e_graficos(df_soc)
        self.gerar_pdf_report(df_analisado)
        print("\n🏆 Pipeline do SOC Preditivo Concluído com Sucesso!")


if __name__ == "__main__":
    detector = SecurityDetector()
    detector.executar_pipeline_completo()
