from __future__ import annotations

import sqlite3
from pathlib import Path

from .contract import Alert
from .serialization import alert_from_json, alert_to_json


class SqliteAlertRepository:
    """Persiste alertas SOC em um banco SQLite."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )
        self._criar_schema()
        self._migrar_schema()
        self._criar_indices()

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
                    severity TEXT,
                    payload_json TEXT NOT NULL
                )
                """
            )

    def _migrar_schema(self) -> None:
        """Aplica evoluções aditivas necessárias ao schema existente."""
        with self._conectar() as conexao:
            colunas = {
                row[1]
                for row in conexao.execute("PRAGMA table_info(alerts)").fetchall()
            }

            if "severity" not in colunas:
                conexao.execute("ALTER TABLE alerts ADD COLUMN severity TEXT")

            registros_sem_severidade = conexao.execute(
                """
                SELECT alert_id, payload_json
                FROM alerts
                WHERE severity IS NULL
                """
            ).fetchall()

            for alert_id, payload_json in registros_sem_severidade:
                alerta = alert_from_json(payload_json)

                conexao.execute(
                    """
                    UPDATE alerts
                    SET severity = ?
                    WHERE alert_id = ?
                    """,
                    (
                        alerta.risk.severity,
                        alert_id,
                    ),
                )

    def _criar_indices(self) -> None:
        with self._conectar() as conexao:
            conexao.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alerts_created_at
                ON alerts(created_at)
                """
            )
            conexao.execute(
                """
                CREATE INDEX IF NOT EXISTS idx_alerts_severity
                ON alerts(severity)
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
                    severity,
                    payload_json
                )
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    alert.alert_id,
                    alert.schema_version,
                    alert.created_at.isoformat(),
                    alert.risk.severity,
                    alert_to_json(alert),
                ),
            )
