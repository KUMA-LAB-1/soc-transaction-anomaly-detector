from __future__ import annotations

from pathlib import Path

from .contract import Alert
from .serialization import alert_to_json


class JsonlAlertRepository:
    """Persiste alertas SOC em formato JSON Lines."""

    def __init__(self, path: str | Path) -> None:
        self.path = Path(path)

    def save(self, alert: Alert) -> None:
        """Acrescenta um alerta serializado ao arquivo JSONL."""
        self.path.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        conteudo = alert_to_json(alert)

        with self.path.open(
            "a",
            encoding="utf-8",
            newline="\n",
        ) as arquivo:
            arquivo.write(conteudo)
            arquivo.write("\n")
