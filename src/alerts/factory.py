from __future__ import annotations

from pathlib import Path

from src.alerts.jsonl_repository import JsonlAlertRepository
from src.alerts.repository import AlertRepository
from src.alerts.sqlite_repository import SqliteAlertRepository

DEFAULT_ALERT_JSONL_PATH = Path("reports/alerts/alerts.jsonl")
DEFAULT_ALERT_SQLITE_PATH = Path("reports/alerts/alerts.db")


def criar_alert_repository(
    storage: str | None,
    *,
    jsonl_path: str | Path | None = None,
    sqlite_path: str | Path | None = None,
) -> AlertRepository | None:
    """Cria o repositório de alertas conforme o backend configurado."""
    if storage is None:
        return None

    storage_normalizado = storage.strip().lower()

    if storage_normalizado in {"", "none", "disabled"}:
        return None

    if storage_normalizado == "jsonl":
        caminho = (
            Path(jsonl_path) if jsonl_path is not None else DEFAULT_ALERT_JSONL_PATH
        )

        return JsonlAlertRepository(caminho)

    if storage_normalizado == "sqlite":
        caminho = (
            Path(sqlite_path) if sqlite_path is not None else DEFAULT_ALERT_SQLITE_PATH
        )

        return SqliteAlertRepository(caminho)

    raise ValueError(f"backend de persistência de alertas não suportado: {storage!r}")
