# src/ingest_mitre.py
import os
from pathlib import (
    Path,  # <-- Importação necessária para manipular caminhos de forma segura
)

import psycopg2
import requests
from dotenv import load_dotenv
from psycopg2.extras import execute_values

# 0. Carrega as variáveis de ambiente apontando para a pasta 'docs'
# __file__ é o caminho absoluto de ingest_mitre.py
# .parent é a pasta 'src'
# .parent.parent é a raiz do seu projeto
BASE_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = BASE_DIR / ".env"

# 1. Carrega as variáveis de ambiente
load_dotenv(dotenv_path=DOTENV_PATH)
MITRE_DATABASE_URL = os.getenv("MITRE_DATABASE_URL")


# URL oficial do MITRE ATT&CK Enterprise (formato STIX/JSON)
MITRE_JSON_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"


def processar_dados_mitre(dados_stix: dict) -> list[tuple]:
    """Transforma objetos STIX do MITRE em registros prontos para persistência."""
    elementos = dados_stix.get("objects", [])

    taticas_nomes = {}
    relacoes_procedimentos = {}
    tecnicas = []

    for obj in elementos:
        tipo = obj.get("type")

        if tipo == "x-mitre-tactic":
            taticas_nomes[obj.get("x_mitre_shortname")] = obj.get("name")

        elif tipo == "relationship" and obj.get("relationship_type") == "uses":
            target_ref = obj.get("target_ref")
            description = obj.get("description")

            if target_ref and description:
                relacoes_procedimentos.setdefault(
                    target_ref,
                    [],
                ).append(description[:200] + "...")

    for obj in elementos:
        if obj.get("type") != "attack-pattern":
            continue

        if obj.get("x_mitre_is_subtechnique", False):
            continue

        external_references = obj.get(
            "external_references",
            [],
        )

        mitre_id = None

        for ref in external_references:
            if ref.get("source_name") == "mitre-attack":
                mitre_id = ref.get("external_id")
                break

        if not mitre_id:
            continue

        nome_tecnica = obj.get("name")

        descricao_tecnica = (
            obj.get(
                "description",
                "Sem descrição disponível.",
            )[:300]
            + "..."
        )

        stix_id = obj.get("id")

        lista_procedimentos = relacoes_procedimentos.get(
            stix_id,
            [],
        )

        if lista_procedimentos:
            procedimentos_consolidados = " | ".join(lista_procedimentos[:3])
        else:
            procedimentos_consolidados = (
                "Nenhum exemplo prático documentado "
                "ou monitoramento padrão recomendado."
            )

        kill_chain_phases = obj.get(
            "kill_chain_phases",
            [],
        )

        for phase in kill_chain_phases:
            fase_codificada = phase.get("phase_name")

            nome_tatica = taticas_nomes.get(
                fase_codificada,
                fase_codificada.replace("-", " ").title(),
            )

            tecnicas.append(
                (
                    mitre_id,
                    nome_tecnica,
                    nome_tatica,
                    descricao_tecnica,
                    procedimentos_consolidados,
                )
            )

    return tecnicas


def baixar_e_processar_mitre() -> list[tuple]:
    """Baixa a base oficial do MITRE ATT&CK e processa os objetos STIX."""
    print("📥 Baixando base de dados oficial do MITRE ATT&CK de forma automatizada...")

    response = requests.get(
        MITRE_JSON_URL,
        timeout=30,
    )

    if response.status_code != 200:
        raise RuntimeError(
            "Falha ao conectar com o repositório do MITRE. "
            f"Status: {response.status_code}"
        )

    print("🧠 Analisando relacionamentos de procedimentos e mitigação (TTPs)...")

    tecnicas = processar_dados_mitre(response.json())

    print(f"✔️ {len(tecnicas)} táticas e técnicas de adversários mapeadas e prontas!")

    return tecnicas


def salvar_no_supabase(
    dados_tecnicas: list[tuple],
    database_url: str | None = None,
) -> None:
    database_url = database_url or MITRE_DATABASE_URL

    if not database_url:
        raise ValueError(
            f"MITRE_DATABASE_URL não encontrada. Caminho configurado: {DOTENV_PATH}"
        )

    print("🔌 Conectando ao PostgreSQL (Supabase)...")

    conn = psycopg2.connect(
        database_url,
        sslmode="require",
    )
    cursor = conn.cursor()

    # Substitui o dataset MITRE de forma atômica.
    # Se a inserção falhar, o TRUNCATE também será revertido.
    print("🧹 Limpando registros antigos de inteligência...")
    cursor.execute("TRUNCATE TABLE tbl_mitre_mapping;")

    query = """
        INSERT INTO tbl_mitre_mapping (
            mitre_id,
            mitre_tecnica,
            mitre_tatica,
            descricao,
            procedimentos
        )
        VALUES %s;
    """

    print(
        "💾 Gravando dados de Inteligência de Ameaças "
        "(Threat Intel) no banco de dados..."
    )

    execute_values(
        cursor,
        query,
        dados_tecnicas,
    )

    conn.commit()
    cursor.close()
    conn.close()
    print(
        "🚀 [SUCESSO] Base do MITRE ATT&CK com Procedimentos ativada e populada no Supabase!"
    )


if __name__ == "__main__":
    try:
        dados = baixar_e_processar_mitre()
        salvar_no_supabase(dados)
    except Exception as e:
        print(f"❌ Ocorreu um erro crítico durante o pipeline de Threat Intel: {e}")
