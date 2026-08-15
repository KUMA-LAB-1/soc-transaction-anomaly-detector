import pytest

from src import db_connector
from src.db_connector import DBConnector


def test_get_engine_rejeita_database_url_ausente(monkeypatch):
    monkeypatch.setattr(
        db_connector,
        "DATABASE_URL",
        None,
    )

    with pytest.raises(
        ValueError,
        match="DATABASE_URL não encontrada",
    ):
        DBConnector.get_engine()


def test_get_raw_connection_rejeita_database_url_ausente(monkeypatch):
    monkeypatch.setattr(
        db_connector,
        "DATABASE_URL",
        None,
    )

    with pytest.raises(
        ValueError,
        match="DATABASE_URL não encontrada",
    ):
        DBConnector.get_raw_connection()


def test_get_engine_forca_sslmode_require(monkeypatch):
    monkeypatch.setattr(
        db_connector,
        "DATABASE_URL",
        "postgresql://usuario:senha@host:5432/banco",
    )

    engine_fake = object()
    chamadas = {}

    def fake_create_engine(url, connect_args):
        chamadas["url"] = url
        chamadas["connect_args"] = connect_args
        return engine_fake

    monkeypatch.setattr(
        db_connector,
        "create_engine",
        fake_create_engine,
    )

    resultado = DBConnector.get_engine()

    assert resultado is engine_fake
    assert chamadas["url"] == "postgresql://usuario:senha@host:5432/banco"
    assert chamadas["connect_args"] == {
        "sslmode": "require",
    }


def test_get_raw_connection_forca_sslmode_require(monkeypatch):
    monkeypatch.setattr(
        db_connector,
        "DATABASE_URL",
        "postgresql://usuario:senha@host:5432/banco",
    )

    conexao_fake = object()
    chamadas = {}

    def fake_connect(url, sslmode):
        chamadas["url"] = url
        chamadas["sslmode"] = sslmode
        return conexao_fake

    monkeypatch.setattr(
        db_connector.psycopg2,
        "connect",
        fake_connect,
    )

    resultado = DBConnector.get_raw_connection()

    assert resultado is conexao_fake
    assert chamadas["url"] == "postgresql://usuario:senha@host:5432/banco"
    assert chamadas["sslmode"] == "require"


def test_get_engine_propaga_erro_de_criacao(monkeypatch, capsys):
    monkeypatch.setattr(
        db_connector,
        "DATABASE_URL",
        "postgresql://teste",
    )

    def criar_engine_com_erro(*args, **kwargs):
        raise RuntimeError("falha simulada no SQLAlchemy")

    monkeypatch.setattr(
        db_connector,
        "create_engine",
        criar_engine_com_erro,
    )

    with pytest.raises(
        RuntimeError,
        match="falha simulada no SQLAlchemy",
    ):
        DBConnector.get_engine()

    saida = capsys.readouterr()

    assert "Falha crítica ao criar o Engine" in saida.out
    assert "falha simulada no SQLAlchemy" in saida.out


def test_get_raw_connection_propaga_erro(monkeypatch, capsys):
    monkeypatch.setattr(
        db_connector,
        "DATABASE_URL",
        "postgresql://teste",
    )

    def conectar_com_erro(*args, **kwargs):
        raise RuntimeError("falha simulada no psycopg2")

    monkeypatch.setattr(
        db_connector.psycopg2,
        "connect",
        conectar_com_erro,
    )

    with pytest.raises(
        RuntimeError,
        match="falha simulada no psycopg2",
    ):
        DBConnector.get_raw_connection()

    saida = capsys.readouterr()

    assert "Falha crítica ao conectar via Psycopg2" in saida.out
    assert "falha simulada no psycopg2" in saida.out
