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
from src.alerts.sqlite_query import SqliteAlertReader
from src.alerts.sqlite_repository import SqliteAlertRepository


def criar_alerta(
    *,
    alert_id: str,
    created_at: datetime,
) -> Alert:
    return Alert(
        alert_id=alert_id,
        created_at=created_at,
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


def test_get_by_id_retorna_alerta_persistido(tmp_path):
    caminho = tmp_path / "alerts.db"

    repository = SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    alerta = criar_alerta(
        alert_id="ALT-001",
        created_at=datetime(
            2026,
            8,
            18,
            21,
            0,
            tzinfo=UTC,
        ),
    )

    repository.save(alerta)

    resultado = reader.get_by_id("ALT-001")

    assert resultado == alerta


def test_get_by_id_retorna_none_quando_alerta_nao_existe(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    resultado = reader.get_by_id("ALT-INEXISTENTE")

    assert resultado is None


def test_list_recent_retorna_alertas_em_ordem_decrescente(tmp_path):
    caminho = tmp_path / "alerts.db"

    repository = SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    alerta_antigo = criar_alerta(
        alert_id="ALT-001",
        created_at=datetime(
            2026,
            8,
            18,
            20,
            0,
            tzinfo=UTC,
        ),
    )

    alerta_intermediario = criar_alerta(
        alert_id="ALT-002",
        created_at=datetime(
            2026,
            8,
            18,
            21,
            0,
            tzinfo=UTC,
        ),
    )

    alerta_recente = criar_alerta(
        alert_id="ALT-003",
        created_at=datetime(
            2026,
            8,
            18,
            22,
            0,
            tzinfo=UTC,
        ),
    )

    repository.save(alerta_antigo)
    repository.save(alerta_intermediario)
    repository.save(alerta_recente)

    resultado = reader.list_recent()

    assert resultado == [
        alerta_recente,
        alerta_intermediario,
        alerta_antigo,
    ]


def test_list_recent_respeita_limit(tmp_path):
    caminho = tmp_path / "alerts.db"

    repository = SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    repository.save(
        criar_alerta(
            alert_id="ALT-001",
            created_at=datetime(
                2026,
                8,
                18,
                20,
                0,
                tzinfo=UTC,
            ),
        )
    )

    repository.save(
        criar_alerta(
            alert_id="ALT-002",
            created_at=datetime(
                2026,
                8,
                18,
                21,
                0,
                tzinfo=UTC,
            ),
        )
    )

    repository.save(
        criar_alerta(
            alert_id="ALT-003",
            created_at=datetime(
                2026,
                8,
                18,
                22,
                0,
                tzinfo=UTC,
            ),
        )
    )

    resultado = reader.list_recent(limit=2)

    assert [alerta.alert_id for alerta in resultado] == [
        "ALT-003",
        "ALT-002",
    ]


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        -100,
    ],
)
def test_list_recent_rejeita_limit_invalido(
    tmp_path,
    limit,
):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    with pytest.raises(
        ValueError,
        match="limit deve ser maior que zero",
    ):
        reader.list_recent(limit=limit)
