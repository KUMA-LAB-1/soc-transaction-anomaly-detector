import json
import sqlite3
from datetime import UTC, datetime

import pytest

from src.alerts.contract import (
    Alert,
    AlertDetection,
    AlertEvent,
    AlertEvidence,
    AlertRisk,
    EvidenceValue,
)
from src.alerts.serialization import alert_to_json
from src.alerts.sqlite_repository import SqliteAlertRepository


def criar_alerta(
    *,
    alert_id: str = "ALT-001",
) -> Alert:
    return Alert(
        alert_id=alert_id,
        created_at=datetime(
            2026,
            8,
            18,
            21,
            0,
            tzinfo=UTC,
        ),
        event=AlertEvent(
            transaction_id=101,
            customer_pseudonym="cliente-001",
            transaction_type="Pix",
            transaction_value=5000.0,
            transaction_timestamp=datetime(
                2026,
                8,
                18,
                20,
                30,
                tzinfo=UTC,
            ),
        ),
        detection=AlertDetection(
            suspicious_probability=0.91,
            anomaly_detected=True,
            anomaly_raw_score=-0.42,
            detector="isolation_forest",
        ),
        risk=AlertRisk(
            score=92.0,
            severity="critical",
        ),
        evidence=AlertEvidence(
            failed_logins=EvidenceValue(
                value=4,
                observed=True,
            ),
            new_device=EvidenceValue(
                value=True,
                observed=True,
            ),
            limit_change=EvidenceValue(
                value=False,
                observed=True,
            ),
            location_change=EvidenceValue(
                value=False,
                observed=True,
            ),
        ),
    )


def test_init_cria_banco_e_schema(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)

    assert caminho.exists()

    with sqlite3.connect(caminho) as conexao:
        tabela = conexao.execute(
            """
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
              AND name = 'alerts'
            """
        ).fetchone()

    assert tabela == ("alerts",)


def test_init_cria_diretorio_pai(tmp_path):
    caminho = tmp_path / "nested" / "soc" / "alerts.db"

    SqliteAlertRepository(caminho)

    assert caminho.exists()


def test_save_persiste_alerta(tmp_path):
    caminho = tmp_path / "alerts.db"
    repository = SqliteAlertRepository(caminho)

    repository.save(criar_alerta())

    with sqlite3.connect(caminho) as conexao:
        registro = conexao.execute(
            """
            SELECT
                alert_id,
                schema_version,
                created_at,
                payload_json
            FROM alerts
            """
        ).fetchone()

    assert registro is not None
    assert registro[0] == "ALT-001"
    assert registro[1] == "1.0"
    assert registro[2] == "2026-08-18T21:00:00+00:00"


def test_save_preserva_payload_json(tmp_path):
    caminho = tmp_path / "alerts.db"
    repository = SqliteAlertRepository(caminho)

    repository.save(criar_alerta())

    with sqlite3.connect(caminho) as conexao:
        payload = conexao.execute("SELECT payload_json FROM alerts").fetchone()[0]

    dados = json.loads(payload)

    assert dados["alert_id"] == "ALT-001"
    assert dados["risk"]["severity"] == "critical"
    assert dados["event"]["transaction_id"] == 101


def test_save_persiste_multiplos_alertas(tmp_path):
    caminho = tmp_path / "alerts.db"
    repository = SqliteAlertRepository(caminho)

    repository.save(
        criar_alerta(
            alert_id="ALT-001",
        )
    )
    repository.save(
        criar_alerta(
            alert_id="ALT-002",
        )
    )

    with sqlite3.connect(caminho) as conexao:
        quantidade = conexao.execute("SELECT COUNT(*) FROM alerts").fetchone()[0]

    assert quantidade == 2


def test_save_rejeita_alert_id_duplicado(tmp_path):
    caminho = tmp_path / "alerts.db"
    repository = SqliteAlertRepository(caminho)

    alerta = criar_alerta()

    repository.save(alerta)

    with pytest.raises(sqlite3.IntegrityError):
        repository.save(alerta)


def test_schema_inclui_coluna_severity(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)

    with sqlite3.connect(caminho) as conexao:
        colunas = {
            row[1] for row in conexao.execute("PRAGMA table_info(alerts)").fetchall()
        }

    assert "severity" in colunas


def test_save_persiste_severity_como_coluna(tmp_path):
    caminho = tmp_path / "alerts.db"
    repository = SqliteAlertRepository(caminho)

    repository.save(criar_alerta())

    with sqlite3.connect(caminho) as conexao:
        severity = conexao.execute(
            """
            SELECT severity
            FROM alerts
            WHERE alert_id = ?
            """,
            ("ALT-001",),
        ).fetchone()[0]

    assert severity == "critical"


def test_init_migra_schema_antigo_e_preserva_dados(tmp_path):
    caminho = tmp_path / "alerts.db"
    alerta = criar_alerta()

    with sqlite3.connect(caminho) as conexao:
        conexao.execute(
            """
            CREATE TABLE alerts (
                alert_id TEXT PRIMARY KEY,
                schema_version TEXT NOT NULL,
                created_at TEXT NOT NULL,
                payload_json TEXT NOT NULL
            )
            """
        )

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
                alerta.alert_id,
                alerta.schema_version,
                alerta.created_at.isoformat(),
                alert_to_json(alerta),
            ),
        )

    SqliteAlertRepository(caminho)

    with sqlite3.connect(caminho) as conexao:
        registro = conexao.execute(
            """
            SELECT alert_id, severity
            FROM alerts
            WHERE alert_id = ?
            """,
            ("ALT-001",),
        ).fetchone()

    assert registro == (
        "ALT-001",
        "critical",
    )


def test_schema_cria_indices_de_consulta(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)

    with sqlite3.connect(caminho) as conexao:
        indices = {
            row[1] for row in conexao.execute("PRAGMA index_list(alerts)").fetchall()
        }

    assert "idx_alerts_created_at" in indices
    assert "idx_alerts_severity" in indices
