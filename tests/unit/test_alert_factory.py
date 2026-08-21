from pathlib import Path

import pytest

from src.alerts.factory import (
    DEFAULT_ALERT_JSONL_PATH,
    DEFAULT_ALERT_SQLITE_PATH,
    criar_alert_repository,
)
from src.alerts.jsonl_repository import JsonlAlertRepository
from src.alerts.sqlite_repository import SqliteAlertRepository


def test_factory_cria_repository_sqlite(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    repository = criar_alert_repository("sqlite")

    assert isinstance(repository, SqliteAlertRepository)


def test_factory_usa_caminho_sqlite_padrao(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    repository = criar_alert_repository("sqlite")

    assert repository.path == DEFAULT_ALERT_SQLITE_PATH


def test_factory_aceita_caminho_sqlite_customizado(tmp_path):
    caminho = tmp_path / "soc" / "alerts.db"

    repository = criar_alert_repository(
        "sqlite",
        sqlite_path=caminho,
    )

    assert repository.path == caminho


@pytest.mark.parametrize(
    "storage",
    [
        None,
        "",
        "none",
        "disabled",
        " NONE ",
    ],
)
def test_factory_desabilita_persistencia(storage):
    repository = criar_alert_repository(storage)

    assert repository is None


def test_factory_cria_repository_jsonl():
    repository = criar_alert_repository("jsonl")

    assert isinstance(repository, JsonlAlertRepository)


def test_factory_aceita_backend_jsonl_sem_diferenciar_maiusculas():
    repository = criar_alert_repository(" JSONL ")

    assert isinstance(repository, JsonlAlertRepository)


def test_factory_usa_caminho_jsonl_padrao():
    repository = criar_alert_repository("jsonl")

    assert repository.path == DEFAULT_ALERT_JSONL_PATH


def test_factory_aceita_caminho_jsonl_customizado(tmp_path):
    caminho = tmp_path / "soc" / "alerts.jsonl"

    repository = criar_alert_repository(
        "jsonl",
        jsonl_path=caminho,
    )

    assert repository.path == caminho


def test_factory_converte_caminho_string_para_path():
    repository = criar_alert_repository(
        "jsonl",
        jsonl_path="custom/alerts.jsonl",
    )

    assert repository.path == Path("custom/alerts.jsonl")


def test_factory_rejeita_backend_desconhecido():
    with pytest.raises(
        ValueError,
        match="backend de persistência de alertas não suportado",
    ):
        criar_alert_repository("orc-database")
