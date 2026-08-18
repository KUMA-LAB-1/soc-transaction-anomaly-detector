from __future__ import annotations

from .config import carregar_alert_persistence_config
from .factory import criar_alert_repository
from .repository import AlertRepository


def criar_alert_repository_configurado() -> AlertRepository | None:
    """Cria o repositório de alertas a partir da configuração do ambiente."""
    config = carregar_alert_persistence_config()

    return criar_alert_repository(
        config.storage,
        jsonl_path=config.jsonl_path,
    )
