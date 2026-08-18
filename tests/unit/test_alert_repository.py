from src.alerts.contract import Alert
from src.alerts.repository import AlertRepository


class FakeAlertRepository:
    def save(self, alert: Alert) -> None:
        self.alert = alert


def test_fake_repository_atende_ao_protocol_em_runtime():
    repository = FakeAlertRepository()

    assert isinstance(repository, AlertRepository)


def test_objeto_sem_save_nao_atende_ao_protocol():
    class RepositorioInvalido:
        pass

    repository = RepositorioInvalido()

    assert not isinstance(repository, AlertRepository)
