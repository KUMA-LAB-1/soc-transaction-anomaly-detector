from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from typing import Any

from .contract import Alert


def _normalizar_valor(valor: Any) -> Any:
    """Converte valores do domínio para tipos compatíveis com JSON."""
    if isinstance(valor, datetime):
        return valor.isoformat()

    if isinstance(valor, tuple):
        return [_normalizar_valor(item) for item in valor]

    if isinstance(valor, list):
        return [_normalizar_valor(item) for item in valor]

    if isinstance(valor, dict):
        return {chave: _normalizar_valor(item) for chave, item in valor.items()}

    return valor


def alert_to_dict(alert: Alert) -> dict[str, Any]:
    """Serializa um Alert para uma estrutura Python compatível com JSON."""
    dados = asdict(alert)
    return _normalizar_valor(dados)


def alert_to_json(
    alert: Alert,
    *,
    indent: int | None = None,
) -> str:
    """Serializa um Alert para JSON UTF-8 preservando caracteres Unicode."""
    return json.dumps(
        alert_to_dict(alert),
        ensure_ascii=False,
        indent=indent,
    )
