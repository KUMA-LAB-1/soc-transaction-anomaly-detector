from __future__ import annotations

from typing import Protocol, runtime_checkable

from .contract import Alert


@runtime_checkable
class AlertRepository(Protocol):
    """Contrato mínimo para persistência de alertas SOC."""

    def save(self, alert: Alert) -> None:
        """Persiste um único alerta."""
        ...
