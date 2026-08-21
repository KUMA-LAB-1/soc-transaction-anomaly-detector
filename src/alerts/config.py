from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from .factory import DEFAULT_ALERT_JSONL_PATH


@dataclass(frozen=True)
class AlertPersistenceConfig:
    storage: str | None
    jsonl_path: Path
    sqlite_path: Path


def carregar_alert_persistence_config() -> AlertPersistenceConfig:
    """Carrega a configuração de persistência de alertas do ambiente."""
    storage = os.getenv("ALERT_STORAGE")

    jsonl_path = Path(
        os.getenv(
            "ALERT_JSONL_PATH",
            str(DEFAULT_ALERT_JSONL_PATH),
        )
    )

    sqlite_path = Path(
        os.getenv(
            "ALERT_SQLITE_PATH",
            "reports/alerts/alerts.db",
        )
    )

    return AlertPersistenceConfig(
        storage=storage,
        jsonl_path=jsonl_path,
        sqlite_path=sqlite_path,
    )
