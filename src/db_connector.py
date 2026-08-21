# src/db_connector.py
import os
from pathlib import Path

import psycopg2
from dotenv import load_dotenv
from sqlalchemy import create_engine

BASE_DIR = Path(__file__).resolve().parent.parent
DOTENV_PATH = BASE_DIR / ".env"

load_dotenv(dotenv_path=DOTENV_PATH)
SOC_DATABASE_URL = os.getenv("SOC_DATABASE_URL")


class DBConnector:
    """
    Classe responsável por gerenciar conexões seguras com o banco utilizado
    pelo runtime principal do pipeline SOC.
    """

    @staticmethod
    def get_engine():
        """Retorna o engine SQLAlchemy utilizado pelo pipeline SOC."""
        if not SOC_DATABASE_URL:
            raise ValueError(
                f"❌ Erro: SOC_DATABASE_URL não encontrada no caminho "
                f"configurado: {DOTENV_PATH}"
            )

        try:
            connect_args = {"sslmode": "require"}

            return create_engine(
                SOC_DATABASE_URL,
                connect_args=connect_args,
            )
        except Exception as e:
            print(f"❌ Falha crítica ao criar o Engine do SQLAlchemy (SSL): {e}")
            raise

    @staticmethod
    def get_raw_connection():
        """Retorna conexão psycopg2 utilizada pelo runtime principal do SOC."""
        if not SOC_DATABASE_URL:
            raise ValueError(
                f"❌ Erro: SOC_DATABASE_URL não encontrada no caminho "
                f"configurado: {DOTENV_PATH}"
            )

        try:
            return psycopg2.connect(
                SOC_DATABASE_URL,
                sslmode="require",
            )
        except Exception as e:
            print(f"❌ Falha crítica ao conectar via Psycopg2 (SSL): {e}")
            raise


if __name__ == "__main__":
    print("🔐 Iniciando handshake SSL e validação de conexões seguras...")

    try:
        engine = DBConnector.get_engine()

        with engine.connect():
            print("🚀 [OK] Canal encriptado via SQLAlchemy estabelecido com sucesso!")

        raw_conn = DBConnector.get_raw_connection()
        raw_conn.close()

        print("🚀 [OK] Canal de conexão direta (Psycopg2 + SSL) validado com sucesso!")
    except Exception as e:
        print(f"❌ Handshake de segurança falhou: {e}")
