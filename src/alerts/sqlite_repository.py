from __future__ import annotations

import sqlite3
from pathlib import Path

from .contract import Alert
from .serialization import alert_to_json


class SqliteAlertRepository:
    """Persiste alertas SOC em um banco SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._criar_schema()

    def _conectar(self) -> sqlite3.Connection:
        return sqlite3.connect(self.path)

    def _criar_schema(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE TABLE IF NOT EXISTS alerts (
                    alert_id TEXT PRIMARY KEY,
                    schema_version TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def save(self, alert: Alert) -> None:
        """Persiste um alerta estruturado no SQLite."""
        with self._conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO alerts (
                    alert_id,
                    schema_version,
                    created_at,
                    payload_json
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    alert.alert_id,
                    alert.schema_version,
                    alert.created_at.isoformat(),
                    alert_to_json(alert),
                ),
            )
