from pathlib import Path

from src.alerts.bootstrap import criar_alert_repository_configurado
from src.alerts.jsonl_repository import JsonlAlertRepository


def test_bootstrap_sem_storage_retorna_none(monkeypatch):
    monkeypatch.delenv("ALERT_STORAGE", raising=False)
    monkeypatch.delenv("ALERT_JSONL_PATH", raising=False)

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
