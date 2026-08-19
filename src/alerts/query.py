from __future__ import annotations

from typing import Protocol, runtime_checkable

from .contract import Alert


@runtime_checkable
class AlertReader(Protocol):
    """Contrato para componentes capazes de consultar alertas SOC."""

    def get_by_id(self, alert_id: str) -> Alert | None:
        """Retorna um alerta pelo identificador ou None quando inexistente."""
        ...

    def list_recent(self, *, limit: int = 100) -> list[Alert]:
        """Retorna os alertas mais recentes, limitados pela quantidade informada."""
        ...
