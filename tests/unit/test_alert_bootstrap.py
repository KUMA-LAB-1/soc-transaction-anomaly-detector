from pathlib import Path

from src.alerts.bootstrap import criar_alert_repository_configurado
from src.alerts.jsonl_repository import JsonlAlertRepository
from src.alerts.sqlite_repository import SqliteAlertRepository


def test_bootstrap_cria_sqlite_repository(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    monkeypatch.setenv("ALERT_STORAGE", "sqlite")
    monkeypatch.delenv("ALERT_SQLITE_PATH", raising=False)

    repository = criar_alert_repository_configurado()

    assert isinstance(repository, SqliteAlertRepository)


def test_bootstrap_sem_storage_retorna_none(monkeypatch):
    monkeypatch.delenv("ALERT_STORAGE", raising=False)
    monkeypatch.delenv("ALERT_JSONL_PATH", raising=False)
    monkeypatch.delenv("ALERT_SQLITE_PATH", raising=False)

    repository = criar_alert_repository_configurado()

    assert repository is None


def test_bootstrap_cria_jsonl_repository(monkeypatch):
    monkeypatch.setenv("ALERT_STORAGE", "jsonl")
    monkeypatch.delenv("ALERT_JSONL_PATH", raising=False)

    repository = criar_alert_repository_configurado()

    assert isinstance(repository, JsonlAlertRepository)


def test_bootstrap_respeita_caminho_jsonl_customizado(monkeypatch):
    monkeypatch.setenv("ALERT_STORAGE", "jsonl")
    monkeypatch.setenv(
        "ALERT_JSONL_PATH",
        "custom/soc-alerts.jsonl",
    )

    repository = criar_alert_repository_configurado()

    assert isinstance(repository, JsonlAlertRepository)
    assert repository.path == Path("custom/soc-alerts.jsonl")


def test_bootstrap_respeita_caminho_sqlite_customizado(
    monkeypatch,
    tmp_path,
):
    caminho = tmp_path / "custom" / "soc-alerts.db"

    monkeypatch.setenv("ALERT_STORAGE", "sqlite")
    monkeypatch.setenv(
        "ALERT_SQLITE_PATH",
        str(caminho),
    )

    repository = criar_alert_repository_configurado()

    assert isinstance(repository, SqliteAlertRepository)
    assert repository.path == caminho
