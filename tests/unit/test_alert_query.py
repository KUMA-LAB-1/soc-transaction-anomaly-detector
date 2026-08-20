from src.alerts.contract import Alert
from src.alerts.query import AlertQueryFilters, AlertReader


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


class ObjetoSemLeitura:
    pass


def test_fake_reader_atende_ao_protocol_em_runtime():
    reader = FakeAlertReader()

    assert isinstance(reader, AlertReader)


def test_objeto_sem_metodos_de_leitura_nao_atende_ao_protocol():
    objeto = ObjetoSemLeitura()

    assert not isinstance(objeto, AlertReader)
