# src/ingest_mitre.py
import os
import requests
import psycopg2
from psycopg2.extras import execute_values
from dotenv import load_dotenv
from pathlib import Path  # <-- Importação necessária para manipular caminhos de forma segura

# 0. Carrega as variáveis de ambiente apontando para a pasta 'docs'
# __file__ é o caminho absoluto de ingest_mitre.py
# .parent é a pasta 'src'
# .parent.parent é a raiz do seu projeto
BASE_DIR = Path(__file__).resolve().parent.parent 
DOTENV_PATH = BASE_DIR / "docs" / ".env"

# 1. Carrega as variáveis de ambiente
load_dotenv(dotenv_path=DOTENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    print(f"❌ Erro: DATABASE_URL não encontrada.")
    print(f"🔍 Caminho tentado: {DOTENV_PATH}")
    exit()

# URL oficial do MITRE ATT&CK Enterprise (formato STIX/JSON)
MITRE_JSON_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"

def baixar_e_processar_mitre():
    print("📥 Baixando base de dados oficial do MITRE ATT&CK de forma automatizada...")
    response = requests.get(MITRE_JSON_URL)
    if response.status_code != 200:
        raise Exception(f"Falha ao conectar com o repositório do MITRE. Status: {response.status_code}")
    
    dados_stix = response.json()
    elementos = dados_stix.get("objects", [])
    
    # Dicionários temporários para mapear relacionamentos e táticas
    taticas_nomes = {}
    relacoes_procedimentos = {}  # Mapeia ID da técnica -> lista de descrições de procedimentos (exemplos reais)
    tecnicas = []
    
    print("🧠 Analisando relacionamentos de procedimentos e mitigação (TTPs)...")
    
    # Passo 1: Mapear nomes de táticas e coletar relações de uso (Procedimentos)
    for obj in elementos:
        tipo = obj.get("type")
        
        # Mapeia código curto de táticas para nome legível
        if tipo == "x-mitre-tactic":
            taticas_nomes[obj.get("x_mitre_shortname")] = obj.get("name")
            
        # Coleta descrições de uso prático (procedimentos relacionando um grupo/software a uma técnica)
        elif tipo == "relationship" and obj.get("relationship_type") == "uses":
            target_ref = obj.get("target_ref")  # Técnica (ex: attack-pattern--...)
            description = obj.get("description")
            
            if target_ref and description:
                if target_ref not in relacoes_procedimentos:
                    relacoes_procedimentos[target_ref] = []
                # Guardamos a descrição do procedimento (limite de caracteres por segurança)
                relacoes_procedimentos[target_ref].append(description[:200] + "...")

    # Passo 2: Filtrar e extrair as técnicas (attack-pattern)
    print("🧩 Estruturando técnicas e associando os procedimentos correspondentes...")
    for obj in elementos:
        if obj.get("type") == "attack-pattern" and not obj.get("x_mitre_is_subtechnique", False):
            # Obtém o ID externo do MITRE (ex: T1110)
            external_references = obj.get("external_references", [])
            mitre_id = None
            for ref in external_references:
                if ref.get("source_name") == "mitre-attack":
                    mitre_id = ref.get("external_id")
                    break
            
            if not mitre_id:
                continue
                
            nome_tecnica = obj.get("name")
            descricao_tecnica = obj.get("description", "Sem descrição disponível.")[:300] + "..."
            
            # Recupera os procedimentos práticos salvos no Passo 1 para esta técnica específica
            stix_id = obj.get("id")
            lista_procedimentos = relacoes_procedimentos.get(stix_id, [])
            
            if lista_procedimentos:
                # Une os 3 principais exemplos de procedimentos reais encontrados
                procedimentos_consolidados = " | ".join(lista_procedimentos[:3])
            else:
                procedimentos_consolidados = "Nenhum exemplo prático documentado ou monitoramento padrão recomendado."

            # Associa a técnica à sua respectiva tática principal (kill chain phase)
            kill_chain_phases = obj.get("kill_chain_phases", [])
            for phase in kill_chain_phases:
                fase_codificada = phase.get("phase_name")
                nome_tatica = taticas_nomes.get(fase_codificada, fase_codificada.replace("-", " ").title())
                
                # Armazena a tupla estruturada para inserção no banco
                tecnicas.append((mitre_id, nome_tecnica, nome_tatica, descricao_tecnica, procedimentos_consolidados))
                
    print(f"✔️ {len(tecnicas)} táticas e técnicas de adversários mapeadas e prontas!")
    return tecnicas

def salvar_no_supabase(dados_tecnicas):
    print("🔌 Conectando ao PostgreSQL (Supabase)...")
    
    # Aqui dizemos explicitamente para o psycopg2 usar SSL
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    cursor = conn.cursor()
    
    print("🛠️ Criando a tabela 'tbl_mitre_mapping' no Supabase...")
    # Criamos a tabela estruturada já contendo o campo de procedimentos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tbl_mitre_mapping (
        mitre_id VARCHAR(15),
        mitre_tecnica VARCHAR(200) NOT NULL,
        mitre_tatica VARCHAR(150) NOT NULL,
        descricao TEXT,
        procedimentos TEXT,
        PRIMARY KEY (mitre_id, mitre_tatica)
    );
    """)
    conn.commit()
    
    # Limpa dados anteriores para evitar duplicações e garantir dados frescos do MITRE
    print("🧹 Limpando registros antigos de inteligência...")
    cursor.execute("TRUNCATE TABLE tbl_mitre_mapping;")
    conn.commit()
    
    # Inserção em lote (Bulk Insert) otimizada
    query = """
        INSERT INTO tbl_mitre_mapping (mitre_id, mitre_tecnica, mitre_tatica, descricao, procedimentos)
        VALUES %s
        ON CONFLICT (mitre_id, mitre_tatica) DO NOTHING;
    """
    
    print("💾 Gravando dados de Inteligência de Ameaças (Threat Intel) no banco de dados...")
    execute_values(cursor, query, dados_tecnicas)
    conn.commit()
    
    cursor.close()
    conn.close()
    print("🚀 [SUCESSO] Base do MITRE ATT&CK com Procedimentos ativada e populada no Supabase!")

if __name__ == "__main__":
    try:
        dados = baixar_e_processar_mitre()
        salvar_no_supabase(dados)
    except Exception as e:
        print(f"❌ Ocorreu um erro crítico durante o pipeline de Threat Intel: {e}")
