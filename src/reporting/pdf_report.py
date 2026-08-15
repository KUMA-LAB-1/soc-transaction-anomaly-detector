import html
from pathlib import Path

import numpy as np
import pandas as pd
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from ..data.columns import resolver_coluna_cliente
from ..threat_intel.mitre import enriquecer_com_mitre


def gerar_relatorio_pdf(
    df_analisado: pd.DataFrame,
    metricas: dict,
    melhor_detector: str | None,
    aviso_amostra_pequena: bool,
    engine,
    pdf_path: str | Path = "reports/Relatorio_Incidente_SOC.pdf",
) -> Path:

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
        Paragraph("RELATÓRIO DE DETECÇÃO DE INCIDENTES - SOC PREDITIVO", titulo_style),
        Paragraph(
            "Análise de ML, validação de modelos e mapeamento MITRE ATT&CK",
            sub_style,
        ),
    ]

    m_reg_preview = metricas.get("regressao", {})
    if aviso_amostra_pequena or (m_reg_preview.get("r2_cv_media", 0) or 0) < 0:
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
    m_clf = metricas.get("classificacao", {})
    m_detector = metricas.get(melhor_detector or "isolation_forest", {})
    m_reg = metricas.get("regressao", {})

    auc_txt = (
        f"{m_clf.get('roc_auc_teste'):.2f}"
        if m_clf.get("roc_auc_teste") is not None
        and not np.isnan(m_clf.get("roc_auc_teste", float("nan")))
        else "N/D"
    )
    r2_txt = (
        f"{m_reg.get('r2_teste'):.2f}" if m_reg.get("r2_teste") is not None else "N/D"
    )
    mae_txt = (
        f"{m_reg.get('mae_teste'):.1f}" if m_reg.get("mae_teste") is not None else "N/D"
    )

    texto_resumo = (
        f"Este relatório documenta {qtd_anomalias} transações sinalizadas por detecção de anomalias "
        f"({(melhor_detector or 'isolation_forest').replace('_', ' ').title()}, contamination={m_detector.get('contamination_usado', 0):.2f}). "
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
                "mudanca_localizacao_flag": row.get("mudanca_localizacao_flag", False),
            }
            intel = enriquecer_com_mitre(
                engine=engine,
                tipo_evento=tipo_evento,
                sinais=sinais,
            )
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
        f"Detector selecionado ({(melhor_detector or 'N/D').replace('_', ' ')}): "
        f"precision={precision_detector:.2f}, recall={recall_detector:.2f}, F1={f1_detector:.2f} "
        f"(rótulo usado somente para auditoria comparativa). "
        f"Regressão de severidade: R² (validação cruzada 5-fold)={r2_cv:.2f}."
    )
    elementos.append(Paragraph(texto_validacao, corpo_style))

    comparacao_info = metricas.get("comparacao_detectores", {}).get("resultados", [])
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

    return pdf_path
