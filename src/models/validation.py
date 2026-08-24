import math

import numpy as np
import pandas as pd

COLUNA_TEMPO_PADRAO = "data_hora_transacao"


def dividir_holdout_temporal(
    df: pd.DataFrame,
    *,
    test_size: float = 0.25,
    coluna_tempo: str = COLUNA_TEMPO_PADRAO,
) -> tuple[np.ndarray, np.ndarray]:
    """Divide registros em passado (treino) e futuro (teste).

    Os índices retornados são posicionais e podem ser utilizados com ``.iloc``.
    A ordenação temporal é estável para preservar uma ordem determinística
    entre registros que possuam o mesmo timestamp.
    """
    if not 0 < test_size < 1:
        raise ValueError("test_size deve estar entre 0 e 1.")

    if coluna_tempo not in df.columns:
        raise ValueError(f"Dataset sem a coluna temporal obrigatória '{coluna_tempo}'.")

    if len(df) < 2:
        raise ValueError("Holdout temporal exige pelo menos 2 registros.")

    timestamps = pd.to_datetime(
        df[coluna_tempo],
        errors="raise",
    )

    ordem = (
        pd.DataFrame(
            {
                "_posicao": np.arange(len(df)),
                "_timestamp": timestamps.to_numpy(),
            }
        )
        .sort_values(
            "_timestamp",
            kind="stable",
        )["_posicao"]
        .to_numpy()
    )

    n_teste = max(
        1,
        math.ceil(len(df) * test_size),
    )
    n_treino = len(df) - n_teste

    if n_treino < 1:
        raise ValueError(
            "Holdout temporal não deixou registros suficientes para treino."
        )

    indices_treino = ordem[:n_treino]
    indices_teste = ordem[n_treino:]

    return indices_treino, indices_teste
