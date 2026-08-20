from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Protocol, runtime_checkable

from .contract import Alert


@dataclass(frozen=True)
class AlertQueryFilters:
    severity: str | None = None
    created_from: datetime | None = None
    created_to: datetime | None = None
    limit: int = 100


@runtime_checkable
class AlertReader(Protocol):
    """Contrato para componentes capazes de consultar alertas SOC."""

    def get_by_id(self, alert_id: str) -> Alert | None:
        """Retorna um alerta pelo identificador ou None quando inexistente."""
        ...

    def list_recent(self, *, limit: int = 100) -> list[Alert]:
        """Retorna os alertas mais recentes, limitados pela quantidade informada."""
        ...

    def search(self, filters: AlertQueryFilters) -> list[Alert]:
        """Consulta alertas utilizando filtros operacionais."""
        ...
