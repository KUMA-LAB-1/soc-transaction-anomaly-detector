# src/db_connector.py
import os
from pathlib import Path
from sqlalchemy import create_engine
import psycopg2
from dotenv import load_dotenv

# 0. Localização segura e padronizada do arquivo de variáveis de ambiente (.env)
BASE_DIR = Path(__file__).resolve().parent.parent 
DOTENV_PATH = BASE_DIR / "docs" / ".env"

# 1. Carrega as variáveis de ambiente com tratamento de caminho
load_dotenv(dotenv_path=DOTENV_PATH)
DATABASE_URL = os.getenv("DATABASE_URL")

class DBConnector:
    """
    Classe responsável por gerenciar conexões seguras com o Supabase,
    garantindo criptografia SSL em trânsito (Defense-in-Depth).
    """
    
    @staticmethod
    def get_engine():
        """
        Retorna o engine do SQLAlchemy configurado obrigatoriamente com SSL,
        ideal para manipulação de grandes volumes de dados via Pandas.
        """
        if not DATABASE_URL:
            raise ValueError(f"❌ Erro: DATABASE_URL não encontrada no caminho configurado: {DOTENV_PATH}")
        
        try:
            # Força o SQLAlchemy a usar SSL nas conexões para mitigar ataques de interceptação (MitM)
            connect_args = {"sslmode": "require"}
            engine = create_engine(DATABASE_URL, connect_args=connect_args)
            return engine
        except Exception as e:
            print(f"❌ Falha crítica ao criar o Engine do SQLAlchemy (SSL): {e}")
            raise

    @staticmethod
    def get_raw_connection():
        """
        Retorna uma conexão direta via psycopg2 encriptada com SSL (sslmode='require')
        para execução direta de transações no banco.
        """
        if not DATABASE_URL:
            raise ValueError(f"❌ Erro: DATABASE_URL não encontrada no caminho configurado: {DOTENV_PATH}")
            
        try:
            # Estabelece a conexão com parâmetro SSL obrigatório
            conn = psycopg2.connect(DATABASE_URL, sslmode="require")
            return conn
        except Exception as e:
            print(f"❌ Falha crítica ao conectar via Psycopg2 (SSL): {e}")
            raise

if __name__ == "__main__":
    # Teste rápido de integridade e conectividade criptografada
    print("🔐 Iniciando handshake SSL e validação de conexões seguras...")
    try:
        engine = DBConnector.get_engine()
        with engine.connect() as conn:
            print("🚀 [OK] Canal encriptado via SQLAlchemy estabelecido com sucesso!")
            
        raw_conn = DBConnector.get_raw_connection()
        raw_conn.close()
        print("🚀 [OK] Canal de conexão direta (Psycopg2 + SSL) validado com sucesso!")
    except Exception as e:
        print(f"❌ Handshake de segurança falhou: {e}")
