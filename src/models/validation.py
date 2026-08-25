import math

import numpy as np
import pandas as pd
from sklearn.model_selection import TimeSeriesSplit

COLUNA_TEMPO_PADRAO = "data_hora_transacao"


def _ordenar_indices_temporais(
    df: pd.DataFrame,
    coluna_tempo: str,
) -> np.ndarray:
    """Retorna posições do DataFrame ordenadas cronologicamente."""
    if coluna_tempo not in df.columns:
        raise ValueError(f"Dataset sem a coluna temporal obrigatória '{coluna_tempo}'.")

    timestamps = pd.to_datetime(
        df[coluna_tempo],
        errors="raise",
    )

    return (
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


def _encontrar_fronteira_temporal_valida(
    timestamps_ordenados: pd.Series,
    corte_desejado: int,
) -> int:
    """Encontra a fronteira temporal válida mais próxima do corte desejado."""
    fronteiras_validas = [
        posicao
        for posicao in range(1, len(timestamps_ordenados))
        if timestamps_ordenados.iloc[posicao - 1] < timestamps_ordenados.iloc[posicao]
    ]

    if not fronteiras_validas:
        raise ValueError(
            "Dataset não possui fronteira temporal válida entre timestamps distintos."
        )

    return min(
        fronteiras_validas,
        key=lambda posicao: (
            abs(posicao - corte_desejado),
            posicao,
        ),
    )


def _encontrar_inicio_teste_temporal_valido(
    timestamps_ordenados: pd.Series,
    inicio_teste: int,
    fim_teste: int,
) -> int:
    """Encontra o primeiro início causalmente válido na janela de teste."""
    for posicao in range(inicio_teste, fim_teste):
        if (
            posicao > 0
            and timestamps_ordenados.iloc[posicao - 1]
            < timestamps_ordenados.iloc[posicao]
        ):
            return posicao

    raise ValueError(
        "Fold temporal não possui fronteira temporal válida dentro da janela de teste."
    )


def dividir_holdout_temporal(
    df: pd.DataFrame,
    *,
    test_size: float = 0.25,
    coluna_tempo: str = COLUNA_TEMPO_PADRAO,
) -> tuple[np.ndarray, np.ndarray]:
    """Divide registros em passado (treino) e futuro (teste).

    Os índices retornados são posicionais e podem ser utilizados com ``.iloc``.
    A ordenação temporal é estável e registros com o mesmo timestamp não são
    divididos entre treino e teste. Quando o corte desejado coincide com um
    grupo empatado, utiliza-se a fronteira temporal válida mais próxima.
    """
    if not 0 < test_size < 1:
        raise ValueError("test_size deve estar entre 0 e 1.")

    if len(df) < 2:
        raise ValueError("Holdout temporal exige pelo menos 2 registros.")

    ordem = _ordenar_indices_temporais(
        df,
        coluna_tempo,
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

    timestamps_ordenados = pd.to_datetime(
        df.iloc[ordem][coluna_tempo],
        errors="raise",
    ).reset_index(drop=True)

    n_treino = _encontrar_fronteira_temporal_valida(
        timestamps_ordenados,
        n_treino,
    )

    indices_treino = ordem[:n_treino]
    indices_teste = ordem[n_treino:]

    return indices_treino, indices_teste


def criar_folds_temporais(
    df: pd.DataFrame,
    *,
    n_splits: int = 3,
    gap: int = 0,
    coluna_tempo: str = COLUNA_TEMPO_PADRAO,
) -> list[tuple[np.ndarray, np.ndarray]]:
    """Cria folds temporais com janela de treino expansiva.

    Registros com o mesmo timestamp não são divididos entre treino e teste.
    Quando necessário, o início do teste avança até a primeira fronteira
    temporal válida dentro da janela original. ``gap`` permanece expresso
    em número de registros.
    """
    if n_splits < 2:
        raise ValueError("n_splits deve ser pelo menos 2.")

    if gap < 0:
        raise ValueError("gap não pode ser negativo.")

    if len(df) <= n_splits:
        raise ValueError(
            "Dataset não possui registros suficientes para os folds temporais."
        )

    ordem = _ordenar_indices_temporais(
        df,
        coluna_tempo,
    )

    timestamps_ordenados = pd.to_datetime(
        df.iloc[ordem][coluna_tempo],
        errors="raise",
    ).reset_index(drop=True)

    splitter = TimeSeriesSplit(
        n_splits=n_splits,
        gap=gap,
    )

    folds = []

    for _, teste_ordenado in splitter.split(ordem):
        inicio_teste_original = int(teste_ordenado[0])
        fim_teste_original = int(teste_ordenado[-1]) + 1

        inicio_teste = _encontrar_inicio_teste_temporal_valido(
            timestamps_ordenados,
            inicio_teste_original,
            fim_teste_original,
        )

        fim_treino = inicio_teste - gap

        treino_ajustado = np.arange(fim_treino)
        teste_ajustado = np.arange(
            inicio_teste,
            fim_teste_original,
        )

        folds.append(
            (
                ordem[treino_ajustado],
                ordem[teste_ajustado],
            )
        )

    return folds
