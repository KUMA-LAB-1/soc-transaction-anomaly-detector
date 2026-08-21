import pandas as pd
import pytest

from src.data.repository import SocDataRepository


class FakeCursor:
    def __init__(self):
        self.executed_query = None
        self.executed_params = None
        self.closed = False

    def execute(self, query, params):
        self.executed_query = query
        self.executed_params = params

    def close(self):
        self.closed = True


class FakeConnection:
    def __init__(self):
        self.cursor_obj = FakeCursor()
        self.committed = False
        self.closed = False

    def cursor(self):
        return self.cursor_obj

    def commit(self):
        self.committed = True

    def close(self):
        self.closed = True


def test_carregar_dataset_soc_retorna_dataframe_preparado(monkeypatch):
    engine_fake = object()
    conexao_fake = FakeConnection()

    df_original = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "cliente-a", "cliente-b"],
            "valor": [100.0, 100.0, None],
        }
    )

    def fake_read_sql_query(query, engine):
        assert query == "SELECT * FROM v_analise_investigacao_soc;"
        assert engine is engine_fake
        return df_original.copy()

    monkeypatch.setattr(
        "src.data.repository.pd.read_sql_query",
        fake_read_sql_query,
    )

    repository = SocDataRepository(
        engine=engine_fake,
        raw_connection_factory=lambda: conexao_fake,
    )

    resultado = repository.carregar_dataset_soc()

    assert len(resultado) == 2
    assert resultado.isnull().sum().sum() == 0


def test_carregar_dataset_soc_registra_auditoria(monkeypatch):
    engine_fake = object()
    conexao_fake = FakeConnection()

    df = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "cliente-b"],
            "valor": [100, 200],
        }
    )

    monkeypatch.setattr(
        "src.data.repository.pd.read_sql_query",
        lambda query, engine: df.copy(),
    )

    repository = SocDataRepository(
        engine=engine_fake,
        raw_connection_factory=lambda: conexao_fake,
    )

    repository.carregar_dataset_soc()

    cursor = conexao_fake.cursor_obj

    assert cursor.executed_query is not None
    assert "INSERT INTO tbl_auditoria_acessos" in cursor.executed_query
    assert cursor.executed_params[1] == "v_analise_investigacao_soc"
    assert cursor.executed_params[2] == 2
    assert (
        cursor.executed_params[3] == "Execução do pipeline de detecção preditiva do SOC"
    )

    assert conexao_fake.committed is True
    assert cursor.closed is True
    assert conexao_fake.closed is True


def test_registrar_auditoria_usa_usuario_do_ambiente(monkeypatch):
    conexao_fake = FakeConnection()

    monkeypatch.setenv(
        "SOC_PIPELINE_USER",
        "usuario-teste",
    )

    repository = SocDataRepository(
        engine=object(),
        raw_connection_factory=lambda: conexao_fake,
    )

    repository.registrar_auditoria(
        view_acessada="view_teste",
        qtd_linhas=10,
        finalidade="teste unitário",
    )

    params = conexao_fake.cursor_obj.executed_params

    assert params[0] == "usuario-teste"
    assert params[1] == "view_teste"
    assert params[2] == 10
    assert params[3] == "teste unitário"


def test_erro_na_auditoria_nao_interrompe_pipeline(capsys):
    def conexao_com_erro():
        raise RuntimeError("banco de auditoria indisponível")

    repository = SocDataRepository(
        engine=object(),
        raw_connection_factory=conexao_com_erro,
    )

    repository.registrar_auditoria(
        view_acessada="view_teste",
        qtd_linhas=10,
        finalidade="teste",
    )

    saida = capsys.readouterr()

    assert "Não foi possível registrar auditoria" in saida.out
    assert "banco de auditoria indisponível" in saida.out


def test_erro_na_leitura_do_dataset_e_propagado(monkeypatch):
    def leitura_com_erro(query, engine):
        raise RuntimeError("falha simulada na leitura")

    monkeypatch.setattr(
        "src.data.repository.pd.read_sql_query",
        leitura_com_erro,
    )

    repository = SocDataRepository(
        engine=object(),
        raw_connection_factory=lambda: FakeConnection(),
    )

    with pytest.raises(
        RuntimeError,
        match="falha simulada na leitura",
    ):
        repository.carregar_dataset_soc()
