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
from src.alerts.query import (
    AlertCursor,
    AlertQueryFilters,
    AlertReader,
)
from src.alerts.sqlite_query import SqliteAlertReader
from src.alerts.sqlite_repository import SqliteAlertRepository


def criar_alerta(
    *,
    alert_id: str,
    created_at: datetime,
    severity: str = "critical",
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
            severity=severity,
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


def test_search_filtra_por_severidade(tmp_path):
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
            severity="medium",
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
            severity="critical",
        )
    )

    resultado = reader.search(
        AlertQueryFilters(
            severity="critical",
        )
    )

    assert [alerta.alert_id for alerta in resultado] == [
        "ALT-002",
    ]


def test_search_filtra_por_periodo(tmp_path):
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

    resultado = reader.search(
        AlertQueryFilters(
            created_from=datetime(
                2026,
                8,
                18,
                20,
                30,
                tzinfo=UTC,
            ),
            created_to=datetime(
                2026,
                8,
                18,
                21,
                30,
                tzinfo=UTC,
            ),
        )
    )

    assert [alerta.alert_id for alerta in resultado] == [
        "ALT-002",
    ]


def test_search_combina_filtros(tmp_path):
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
            severity="critical",
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
            severity="critical",
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
            severity="medium",
        )
    )

    resultado = reader.search(
        AlertQueryFilters(
            severity="critical",
            created_from=datetime(
                2026,
                8,
                18,
                20,
                30,
                tzinfo=UTC,
            ),
            limit=10,
        )
    )

    assert [alerta.alert_id for alerta in resultado] == [
        "ALT-002",
    ]


def test_search_respeita_limit(tmp_path):
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

    resultado = reader.search(AlertQueryFilters(limit=1))

    assert len(resultado) == 1
    assert resultado[0].alert_id == "ALT-002"


def test_search_sem_filtros_equivale_a_lista_recente(tmp_path):
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

    resultado = reader.search(AlertQueryFilters())

    esperado = reader.list_recent()

    assert resultado == esperado


@pytest.mark.parametrize(
    "limit",
    [
        0,
        -1,
        -100,
    ],
)
def test_search_rejeita_limit_invalido(
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
        reader.search(
            AlertQueryFilters(
                limit=limit,
            )
        )


def test_search_rejeita_periodo_invertido(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    with pytest.raises(
        ValueError,
        match="created_from não pode ser posterior a created_to",
    ):
        reader.search(
            AlertQueryFilters(
                created_from=datetime(
                    2026,
                    8,
                    19,
                    10,
                    0,
                    tzinfo=UTC,
                ),
                created_to=datetime(
                    2026,
                    8,
                    18,
                    10,
                    0,
                    tzinfo=UTC,
                ),
            )
        )


def test_sqlite_reader_atende_ao_protocol(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    assert isinstance(reader, AlertReader)


def test_search_page_retorna_primeira_pagina_e_cursor(tmp_path):
    caminho = tmp_path / "alerts.db"

    repository = SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    for indice, hora in enumerate(
        [20, 21, 22],
        start=1,
    ):
        repository.save(
            criar_alerta(
                alert_id=f"ALT-00{indice}",
                created_at=datetime(
                    2026,
                    8,
                    20,
                    hora,
                    0,
                    tzinfo=UTC,
                ),
            )
        )

    page = reader.search_page(AlertQueryFilters(limit=2))

    assert [alerta.alert_id for alerta in page.items] == [
        "ALT-003",
        "ALT-002",
    ]

    assert page.next_cursor == AlertCursor(
        created_at=datetime(
            2026,
            8,
            20,
            21,
            0,
            tzinfo=UTC,
        ),
        alert_id="ALT-002",
    )


def test_search_page_retorna_segunda_pagina_sem_repetir_alertas(tmp_path):
    caminho = tmp_path / "alerts.db"

    repository = SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    for indice, hora in enumerate(
        [20, 21, 22],
        start=1,
    ):
        repository.save(
            criar_alerta(
                alert_id=f"ALT-00{indice}",
                created_at=datetime(
                    2026,
                    8,
                    20,
                    hora,
                    0,
                    tzinfo=UTC,
                ),
            )
        )

    primeira = reader.search_page(AlertQueryFilters(limit=2))

    segunda = reader.search_page(
        AlertQueryFilters(limit=2),
        cursor=primeira.next_cursor,
    )

    assert [alerta.alert_id for alerta in primeira.items] == [
        "ALT-003",
        "ALT-002",
    ]

    assert [alerta.alert_id for alerta in segunda.items] == [
        "ALT-001",
    ]

    assert segunda.next_cursor is None


def test_search_page_desempata_por_alert_id(tmp_path):
    caminho = tmp_path / "alerts.db"

    repository = SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    created_at = datetime(
        2026,
        8,
        20,
        21,
        0,
        tzinfo=UTC,
    )

    for alert_id in [
        "ALT-001",
        "ALT-002",
        "ALT-003",
    ]:
        repository.save(
            criar_alerta(
                alert_id=alert_id,
                created_at=created_at,
            )
        )

    primeira = reader.search_page(AlertQueryFilters(limit=2))

    segunda = reader.search_page(
        AlertQueryFilters(limit=2),
        cursor=primeira.next_cursor,
    )

    assert [alerta.alert_id for alerta in primeira.items] == [
        "ALT-003",
        "ALT-002",
    ]

    assert [alerta.alert_id for alerta in segunda.items] == [
        "ALT-001",
    ]


def test_search_page_sem_resultados_retorna_pagina_vazia(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    page = reader.search_page(AlertQueryFilters(limit=10))

    assert page.items == ()
    assert page.next_cursor is None


def test_search_page_combina_cursor_com_filtro_de_severidade(tmp_path):
    caminho = tmp_path / "alerts.db"

    repository = SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    repository.save(
        criar_alerta(
            alert_id="ALT-001",
            created_at=datetime(2026, 8, 20, 20, 0, tzinfo=UTC),
            severity="critical",
        )
    )
    repository.save(
        criar_alerta(
            alert_id="ALT-002",
            created_at=datetime(2026, 8, 20, 21, 0, tzinfo=UTC),
            severity="medium",
        )
    )
    repository.save(
        criar_alerta(
            alert_id="ALT-003",
            created_at=datetime(2026, 8, 20, 22, 0, tzinfo=UTC),
            severity="critical",
        )
    )

    primeira = reader.search_page(
        AlertQueryFilters(
            severity="critical",
            limit=1,
        )
    )

    segunda = reader.search_page(
        AlertQueryFilters(
            severity="critical",
            limit=1,
        ),
        cursor=primeira.next_cursor,
    )

    assert [alerta.alert_id for alerta in primeira.items] == [
        "ALT-003",
    ]
    assert [alerta.alert_id for alerta in segunda.items] == [
        "ALT-001",
    ]
    assert segunda.next_cursor is None


def test_search_page_combina_cursor_com_periodo(tmp_path):
    caminho = tmp_path / "alerts.db"

    repository = SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    for indice, hora in enumerate(
        [19, 20, 21, 22],
        start=1,
    ):
        repository.save(
            criar_alerta(
                alert_id=f"ALT-00{indice}",
                created_at=datetime(
                    2026,
                    8,
                    20,
                    hora,
                    0,
                    tzinfo=UTC,
                ),
            )
        )

    filters = AlertQueryFilters(
        created_from=datetime(
            2026,
            8,
            20,
            20,
            0,
            tzinfo=UTC,
        ),
        created_to=datetime(
            2026,
            8,
            20,
            22,
            0,
            tzinfo=UTC,
        ),
        limit=2,
    )

    primeira = reader.search_page(filters)

    segunda = reader.search_page(
        filters,
        cursor=primeira.next_cursor,
    )

    assert [alerta.alert_id for alerta in primeira.items] == [
        "ALT-004",
        "ALT-003",
    ]

    assert [alerta.alert_id for alerta in segunda.items] == [
        "ALT-002",
    ]


def test_search_page_rejeita_limit_invalido(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    with pytest.raises(
        ValueError,
        match="limit deve ser maior que zero",
    ):
        reader.search_page(AlertQueryFilters(limit=0))


def test_search_page_rejeita_periodo_invertido(tmp_path):
    caminho = tmp_path / "alerts.db"

    SqliteAlertRepository(caminho)
    reader = SqliteAlertReader(caminho)

    with pytest.raises(
        ValueError,
        match="created_from não pode ser posterior a created_to",
    ):
        reader.search_page(
            AlertQueryFilters(
                created_from=datetime(
                    2026,
                    8,
                    21,
                    10,
                    0,
                    tzinfo=UTC,
                ),
                created_to=datetime(
                    2026,
                    8,
                    20,
                    10,
                    0,
                    tzinfo=UTC,
                ),
            )
        )
