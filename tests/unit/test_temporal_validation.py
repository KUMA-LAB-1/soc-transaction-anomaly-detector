import numpy as np
import pandas as pd
import pytest

from src.models.validation import dividir_holdout_temporal


def criar_dataset_temporal() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "valor": [40, 10, 30, 20],
            "data_hora_transacao": [
                "2026-08-04 10:00:00",
                "2026-08-01 10:00:00",
                "2026-08-03 10:00:00",
                "2026-08-02 10:00:00",
            ],
        }
    )


def test_holdout_temporal_separa_passado_e_futuro():
    df = criar_dataset_temporal()

    treino, teste = dividir_holdout_temporal(
        df,
        test_size=0.25,
    )

    assert treino.tolist() == [1, 3, 2]
    assert teste.tolist() == [0]


def test_holdout_temporal_respeita_proporcao():
    df = pd.DataFrame(
        {
            "data_hora_transacao": pd.date_range(
                "2026-01-01",
                periods=40,
                freq="h",
            )
        }
    )

    treino, teste = dividir_holdout_temporal(
        df,
        test_size=0.25,
    )

    assert len(treino) == 30
    assert len(teste) == 10


def test_holdout_temporal_garante_ordem_cronologica():
    df = criar_dataset_temporal()

    treino, teste = dividir_holdout_temporal(df)

    timestamps = pd.to_datetime(df["data_hora_transacao"])

    assert timestamps.iloc[treino].max() <= timestamps.iloc[teste].min()


def test_holdout_temporal_preserva_ordem_em_empates():
    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-01 10:00:00",
                "2026-08-01 10:00:00",
                "2026-08-01 11:00:00",
                "2026-08-01 12:00:00",
            ]
        }
    )

    treino, teste = dividir_holdout_temporal(
        df,
        test_size=0.5,
    )

    assert treino.tolist() == [0, 1]
    assert teste.tolist() == [2, 3]


@pytest.mark.parametrize(
    "test_size",
    [
        0,
        1,
        -0.1,
        1.1,
    ],
)
def test_holdout_temporal_rejeita_test_size_invalido(test_size):
    df = criar_dataset_temporal()

    with pytest.raises(
        ValueError,
        match="test_size deve estar entre 0 e 1",
    ):
        dividir_holdout_temporal(
            df,
            test_size=test_size,
        )


def test_holdout_temporal_exige_coluna_temporal():
    df = pd.DataFrame(
        {
            "valor": [1, 2, 3],
        }
    )

    with pytest.raises(
        ValueError,
        match="coluna temporal obrigatória",
    ):
        dividir_holdout_temporal(df)


def test_holdout_temporal_exige_ao_menos_dois_registros():
    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-01 10:00:00",
            ]
        }
    )

    with pytest.raises(
        ValueError,
        match="pelo menos 2 registros",
    ):
        dividir_holdout_temporal(df)


def test_holdout_temporal_retorna_indices_numpy():
    df = criar_dataset_temporal()

    treino, teste = dividir_holdout_temporal(df)

    assert isinstance(treino, np.ndarray)
    assert isinstance(teste, np.ndarray)


def test_holdout_temporal_rejeita_divisao_sem_amostras_de_treino():
    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-01 10:00:00",
                "2026-08-01 11:00:00",
            ]
        }
    )

    with pytest.raises(
        ValueError,
        match="não deixou registros suficientes para treino",
    ):
        dividir_holdout_temporal(
            df,
            test_size=0.75,
        )


def test_holdout_temporal_rejeita_timestamp_invalido():
    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-01 10:00:00",
                "timestamp-invalido",
            ]
        }
    )

    with pytest.raises(ValueError):
        dividir_holdout_temporal(df)
