from __future__ import annotations

import sqlite3
from pathlib import Path

from .contract import Alert
from .query import AlertQueryFilters
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

    def search(
        self,
        filters: AlertQueryFilters,
    ) -> list[Alert]:
        """Consulta alertas utilizando filtros operacionais."""
        if filters.limit <= 0:
            raise ValueError("limit deve ser maior que zero")

        if (
            filters.created_from is not None
            and filters.created_to is not None
            and filters.created_from > filters.created_to
        ):
            raise ValueError("created_from não pode ser posterior a created_to")

        conditions: list[str] = []
        params: list[object] = []

        if filters.severity is not None:
            conditions.append("severity = ?")
            params.append(filters.severity)

        if filters.created_from is not None:
            conditions.append("created_at >= ?")
            params.append(filters.created_from.isoformat())

        if filters.created_to is not None:
            conditions.append("created_at <= ?")
            params.append(filters.created_to.isoformat())

        where_clause = ""

        if conditions:
            where_clause = "WHERE " + " AND ".join(conditions)

        params.append(filters.limit)

        query = f"""
            SELECT payload_json
            FROM alerts
            {where_clause}
            ORDER BY created_at DESC, alert_id DESC
            LIMIT ?
        """

        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                query,
                params,
            ).fetchall()

        return [alert_from_json(row[0]) for row in rows]
