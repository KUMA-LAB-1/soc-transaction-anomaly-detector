import html
import re

from sqlalchemy import text


def determinar_padrao_por_correlacao(sinais: dict) -> tuple[str | None, str | None]:
    """Determina uma técnica MITRE a partir de sinais comportamentais."""
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
            "mudança de localização entre acessos recentes "
            "(uso de credencial fora do padrão)",
        )

    return None, None


def limpar_texto_mitre(texto: str | None) -> str:
    """Sanitiza o texto MITRE antes de utilizá-lo no relatório."""
    if not texto:
        return "Nenhum procedimento de mitigação listado."

    texto = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", texto)
    texto = re.sub(r"\(Citation:[^)]*\)", "", texto)
    texto = re.sub(r"\s+", " ", texto).strip()

    if len(texto) > 450:
        texto = texto[:450].rsplit(" ", 1)[0] + "…"

    return html.escape(texto)


def enriquecer_com_mitre(
    engine,
    tipo_evento: str,
    sinais: dict | None = None,
) -> dict:
    """Enriquece um evento com dados MITRE ATT&CK do banco ou fallback local."""
    sinais = sinais or {}

    termo_busca, criterio = determinar_padrao_por_correlacao(sinais)

    if not termo_busca:
        criterio = "tipo de transação (fallback, sem correlação de log disponível)"

        if "Pix" in tipo_evento:
            termo_busca = "%T1565%"
        elif "Transferência" in tipo_evento:
            termo_busca = "%T1043%"
        else:
            termo_busca = "%T1110%"

    try:
        query = text(
            """
            SELECT mitre_id, mitre_tecnica, mitre_tatica, procedimentos
            FROM tbl_mitre_mapping
            WHERE mitre_id ILIKE :termo OR mitre_tecnica ILIKE :termo
            ORDER BY mitre_id
            LIMIT 1;
            """
        )

        with engine.connect() as conn:
            result = conn.execute(
                query,
                {"termo": termo_busca},
            ).fetchone()

        if result:
            return {
                "mitre_id": html.escape(str(result[0])),
                "tecnica": html.escape(str(result[1])),
                "tatica": html.escape(str(result[2])),
                "procedimentos": limpar_texto_mitre(result[3]),
                "fonte": "banco de dados (dinâmico)",
                "criterio": criterio,
            }

    except Exception as exc:
        print(
            "⚠️ Alerta ao consultar Threat Intel no banco: "
            f"{exc}. Usando mapeamento local resiliente."
        )

    if "Pix" in tipo_evento:
        return {
            "mitre_id": "T1565.001",
            "tecnica": (
                "Manipulação de Dados: Transferência Financeira Não Autorizada"
            ),
            "tatica": "Impacto / Roubo de Ativos",
            "procedimentos": (
                "Aplicar MFA mandatório para transações fora do horário comercial."
            ),
            "fonte": "fallback local",
            "criterio": criterio,
        }

    return {
        "mitre_id": "T1110.001",
        "tecnica": ("Ataque de Força Bruta (Brute Force Credential Stuffing)"),
        "tatica": "Acesso Inicial",
        "procedimentos": (
            "Bloquear temporariamente o IP de origem e forçar redefinição de senha."
        ),
        "fonte": "fallback local",
        "criterio": criterio,
    }
