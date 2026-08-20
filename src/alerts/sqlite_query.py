from __future__ import annotations

import sqlite3
from pathlib import Path

from .contract import Alert
from .query import AlertCursor, AlertPage, AlertQueryFilters
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

        created_from = (
            filters.created_from.isoformat()
            if filters.created_from is not None
            else None
        )

        created_to = (
            filters.created_to.isoformat() if filters.created_to is not None else None
        )

        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM alerts
                WHERE (? IS NULL OR severity = ?)
                AND (? IS NULL OR created_at >= ?)
                AND (? IS NULL OR created_at <= ?)
                ORDER BY created_at DESC, alert_id DESC
                LIMIT ?
                """,
                (
                    filters.severity,
                    filters.severity,
                    created_from,
                    created_from,
                    created_to,
                    created_to,
                    filters.limit,
                ),
            ).fetchall()

        return [alert_from_json(row[0]) for row in rows]

    def search_page(
        self,
        filters: AlertQueryFilters,
        *,
        cursor: AlertCursor | None = None,
    ) -> AlertPage:
        """Consulta uma página determinística de alertas."""
        if filters.limit <= 0:
            raise ValueError("limit deve ser maior que zero")

        if (
            filters.created_from is not None
            and filters.created_to is not None
            and filters.created_from > filters.created_to
        ):
            raise ValueError("created_from não pode ser posterior a created_to")

        created_from = (
            filters.created_from.isoformat()
            if filters.created_from is not None
            else None
        )

        created_to = (
            filters.created_to.isoformat() if filters.created_to is not None else None
        )

        cursor_created_at = (
            cursor.created_at.isoformat() if cursor is not None else None
        )

        cursor_alert_id = cursor.alert_id if cursor is not None else None

        with sqlite3.connect(self.path) as connection:
            rows = connection.execute(
                """
                SELECT payload_json
                FROM alerts
                WHERE (? IS NULL OR severity = ?)
                AND (? IS NULL OR created_at >= ?)
                AND (? IS NULL OR created_at <= ?)
                AND (
                        ? IS NULL
                        OR created_at < ?
                        OR (
                            created_at = ?
                            AND alert_id < ?
                        )
                )
                ORDER BY created_at DESC, alert_id DESC
                LIMIT ?
                """,
                (
                    filters.severity,
                    filters.severity,
                    created_from,
                    created_from,
                    created_to,
                    created_to,
                    cursor_created_at,
                    cursor_created_at,
                    cursor_created_at,
                    cursor_alert_id,
                    filters.limit + 1,
                ),
            ).fetchall()

        has_next_page = len(rows) > filters.limit

        page_rows = rows[: filters.limit]

        items = tuple(alert_from_json(row[0]) for row in page_rows)

        next_cursor = None

        if has_next_page and items:
            ultimo_alerta = items[-1]

            next_cursor = AlertCursor(
                created_at=ultimo_alerta.created_at,
                alert_id=ultimo_alerta.alert_id,
            )

        return AlertPage(
            items=items,
            next_cursor=next_cursor,
        )
