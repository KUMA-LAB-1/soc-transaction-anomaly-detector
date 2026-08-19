from __future__ import annotations

import sqlite3
from pathlib import Path

from .contract import Alert
from .serialization import alert_from_json


class SqliteAlertReader:
    """Consulta alertas SOC persistidos em SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def get_by_id(self, alert_id: str) -> Alert | None:
        """Retorna um alerta pelo identificador ou None quando inexistente."""
        with sqlite3.connect(self.path) as connection:
            row = connection.execute(
                """
                SELECT payload_json
                FROM alerts
                WHERE alert_id = ?
                """,
                (alert_id,),
            ).fetchone()

        if row is None:
            return None

        return alert_from_json(row[0])

    def list_recent(self, *, limit: int = 100) -> list[Alert]:
        """Retorna os alertas mais recentes."""
        if limit <= 0:
            raise ValueError("limit deve ser maior que zero")

        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM alerts
                ORDER BY created_at DESC, alert_id DESC
                LIMIT ?
                """,
                (limit,),
            ).fetchall()

        return [alert_from_json(row[0]) for row in rows]
