import json
from datetime import UTC, datetime
from pathlib import Path


def salvar_historico_metricas(
    metricas: dict,
    aviso_amostra_pequena: bool,
    caminho: str | Path = "reports/historico_metricas.jsonl",
) -> Path:
    """Registra as métricas do pipeline em formato JSON Lines."""
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    registro = {
        "timestamp": datetime.now(UTC).isoformat(),
        "amostra_pequena": aviso_amostra_pequena,
        **metricas,
    }

    with caminho.open("a", encoding="utf-8") as arquivo:
        arquivo.write(
            json.dumps(
                registro,
                ensure_ascii=False,
                default=str,
            )
            + "\n"
        )

    print(f"📈 Métricas registradas em {caminho}")

    return caminho
