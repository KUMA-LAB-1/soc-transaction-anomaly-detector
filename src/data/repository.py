import getpass
import os
from collections.abc import Callable

import pandas as pd

from .validation import validar_e_preparar_dataset


class SocDataRepository:
    """Responsável por leitura do dataset SOC e registro de auditoria."""

    def __init__(
        self,
        engine,
        raw_connection_factory: Callable,
    ):
        self.engine = engine
        self.raw_connection_factory = raw_connection_factory

    def carregar_dataset_soc(self) -> pd.DataFrame:
        """Carrega e prepara o dataset principal utilizado pelo pipeline."""
        query_view = "SELECT * FROM v_analise_investigacao_soc;"

        try:
            df = pd.read_sql_query(
                query_view,
                self.engine,
            )

            df = validar_e_preparar_dataset(df)

            self.registrar_auditoria(
                view_acessada="v_analise_investigacao_soc",
                qtd_linhas=len(df),
                finalidade="Execução do pipeline de detecção preditiva do SOC",
            )

            return df

        except Exception as exc:
            print(f"❌ Erro na leitura segura do banco: {exc}")
            raise

    def registrar_auditoria(
        self,
        view_acessada: str,
        qtd_linhas: int,
        finalidade: str,
    ) -> None:
        """Registra o acesso ao dataset para fins de accountability."""
        try:
            usuario = (
                os.getenv("SOC_PIPELINE_USER")
                or getpass.getuser()
                or "pipeline_automatizado"
            )

            conn = self.raw_connection_factory()
            cur = conn.cursor()

            cur.execute(
                "INSERT INTO tbl_auditoria_acessos "
                "(usuario_execucao, view_ou_tabela_acessada, "
                "qtd_linhas_retornadas, finalidade) "
                "VALUES (%s, %s, %s, %s)",
                (
                    usuario,
                    view_acessada,
                    int(qtd_linhas),
                    finalidade,
                ),
            )

            conn.commit()
            cur.close()
            conn.close()

        except Exception as exc:
            print(
                "⚠️ Não foi possível registrar auditoria de acesso "
                "(tabela existe? rode 08_hardening_e_correlacao.sql): "
                f"{exc}"
            )
