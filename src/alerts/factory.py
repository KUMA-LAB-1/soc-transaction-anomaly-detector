from __future__ import annotations

from pathlib import Path

from src.alerts.jsonl_repository import JsonlAlertRepository
from src.alerts.repository import AlertRepository

DEFAULT_ALERT_JSONL_PATH = Path("reports/alerts/alerts.jsonl")


def criar_alert_repository(
    storage: str | None,
    *,
    jsonl_path: str | Path | None = None,
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

    raise ValueError(f"backend de persistência de alertas não suportado: {storage!r}")
