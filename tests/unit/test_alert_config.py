from pathlib import Path

from src.alerts.config import (
    AlertPersistenceConfig,
    carregar_alert_persistence_config,
)
from src.alerts.factory import DEFAULT_ALERT_JSONL_PATH


def test_config_sem_variaveis_usa_storage_none(monkeypatch):
    monkeypatch.delenv("ALERT_STORAGE", raising=False)
    monkeypatch.delenv("ALERT_JSONL_PATH", raising=False)

    config = carregar_alert_persistence_config()

    assert config.storage is None
    assert config.jsonl_path == DEFAULT_ALERT_JSONL_PATH


def test_config_carrega_backend_do_ambiente(monkeypatch):
    monkeypatch.setenv("ALERT_STORAGE", "jsonl")
    monkeypatch.delenv("ALERT_JSONL_PATH", raising=False)

    config = carregar_alert_persistence_config()

    assert config.storage == "jsonl"


def test_config_carrega_caminho_jsonl_customizado(monkeypatch):
    monkeypatch.setenv(
        "ALERT_JSONL_PATH",
        "custom/alerts.jsonl",
    )

    config = carregar_alert_persistence_config()

    assert config.jsonl_path == Path("custom/alerts.jsonl")


def test_config_e_imutavel():
    config = AlertPersistenceConfig(
        storage="jsonl",
        jsonl_path=Path("alerts.jsonl"),
    )

    assert config.storage == "jsonl"
    assert config.jsonl_path == Path("alerts.jsonl")
