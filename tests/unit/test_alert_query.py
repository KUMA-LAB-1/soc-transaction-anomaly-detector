from datetime import UTC, datetime

import pytest

from src.alerts.contract import Alert
from src.alerts.query import (
    AlertCursor,
    AlertPage,
    AlertQueryFilters,
    AlertReader,
)


class FakeAlertReader:
    def get_by_id(self, alert_id: str) -> Alert | None:
        return None

    def list_recent(self, *, limit: int = 100) -> list[Alert]:
        return []

    def search(
        self,
        filters: AlertQueryFilters,
    ) -> list[Alert]:
        return []

    def search_page(
        self,
        filters: AlertQueryFilters,
        *,
        cursor: AlertCursor | None = None,
    ) -> AlertPage:
        return AlertPage(
            items=(),
            next_cursor=None,
        )


class ObjetoSemLeitura:
    pass


def test_fake_reader_atende_ao_protocol_em_runtime():
    reader = FakeAlertReader()

    assert isinstance(reader, AlertReader)


def test_objeto_sem_metodos_de_leitura_nao_atende_ao_protocol():
    objeto = ObjetoSemLeitura()

    assert not isinstance(objeto, AlertReader)


def test_alert_cursor_e_imutavel():
    cursor = AlertCursor(
        created_at=datetime(
            2026,
            8,
            20,
            10,
            0,
            tzinfo=UTC,
        ),
        alert_id="ALT-001",
    )

    with pytest.raises(AttributeError):
        cursor.alert_id = "ALT-002"


def test_alert_page_armazena_itens_e_cursor():
    cursor = AlertCursor(
        created_at=datetime(
            2026,
            8,
            20,
            10,
            0,
            tzinfo=UTC,
        ),
        alert_id="ALT-001",
    )

    page = AlertPage(
        items=(),
        next_cursor=cursor,
    )

    assert page.items == ()
    assert page.next_cursor == cursor


def test_alert_page_sem_proxima_pagina_usa_none():
    page = AlertPage(items=())

    assert page.next_cursor is None
