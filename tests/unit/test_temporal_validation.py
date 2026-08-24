import numpy as np
import pandas as pd
import pytest

from src.models.validation import (
    criar_folds_temporais,
    dividir_holdout_temporal,
)


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


def test_cv_temporal_cria_quantidade_esperada_de_folds():
    df = pd.DataFrame(
        {
            "data_hora_transacao": pd.date_range(
                "2026-01-01",
                periods=20,
                freq="h",
            )
        }
    )

    folds = criar_folds_temporais(
        df,
        n_splits=3,
    )

    assert len(folds) == 3


def test_cv_temporal_usa_janela_de_treino_expansiva():
    df = pd.DataFrame(
        {
            "data_hora_transacao": pd.date_range(
                "2026-01-01",
                periods=20,
                freq="h",
            )
        }
    )

    folds = criar_folds_temporais(
        df,
        n_splits=3,
    )

    tamanhos_treino = [len(indices_treino) for indices_treino, _ in folds]

    assert tamanhos_treino == sorted(tamanhos_treino)
    assert len(set(tamanhos_treino)) == len(tamanhos_treino)


def test_cv_temporal_treina_sempre_antes_do_teste():
    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-04 10:00:00",
                "2026-08-01 10:00:00",
                "2026-08-06 10:00:00",
                "2026-08-02 10:00:00",
                "2026-08-05 10:00:00",
                "2026-08-03 10:00:00",
                "2026-08-07 10:00:00",
                "2026-08-08 10:00:00",
            ]
        }
    )

    folds = criar_folds_temporais(
        df,
        n_splits=3,
    )

    timestamps = pd.to_datetime(df["data_hora_transacao"])

    for treino, teste in folds:
        assert timestamps.iloc[treino].max() <= timestamps.iloc[teste].min()


def test_cv_temporal_retorna_indices_do_dataframe_original():
    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-04 10:00:00",
                "2026-08-01 10:00:00",
                "2026-08-03 10:00:00",
                "2026-08-02 10:00:00",
                "2026-08-05 10:00:00",
                "2026-08-06 10:00:00",
            ]
        }
    )

    folds = criar_folds_temporais(
        df,
        n_splits=2,
    )

    primeiro_treino, primeiro_teste = folds[0]

    assert primeiro_treino.tolist() == [1, 3]
    assert primeiro_teste.tolist() == [2, 0]


def test_cv_temporal_respeita_gap():
    df = pd.DataFrame(
        {
            "data_hora_transacao": pd.date_range(
                "2026-01-01",
                periods=12,
                freq="h",
            )
        }
    )

    folds_sem_gap = criar_folds_temporais(
        df,
        n_splits=3,
        gap=0,
    )

    folds_com_gap = criar_folds_temporais(
        df,
        n_splits=3,
        gap=1,
    )

    for (treino_sem_gap, _), (treino_com_gap, _) in zip(
        folds_sem_gap,
        folds_com_gap,
        strict=True,
    ):
        assert len(treino_com_gap) == len(treino_sem_gap) - 1


@pytest.mark.parametrize(
    "n_splits",
    [
        0,
        1,
        -1,
    ],
)
def test_cv_temporal_rejeita_numero_invalido_de_folds(n_splits):
    df = criar_dataset_temporal()

    with pytest.raises(
        ValueError,
        match="n_splits deve ser pelo menos 2",
    ):
        criar_folds_temporais(
            df,
            n_splits=n_splits,
        )


def test_cv_temporal_rejeita_gap_negativo():
    df = criar_dataset_temporal()

    with pytest.raises(
        ValueError,
        match="gap não pode ser negativo",
    ):
        criar_folds_temporais(
            df,
            gap=-1,
        )


def test_cv_temporal_rejeita_dataset_pequeno_demais():
    df = pd.DataFrame(
        {
            "data_hora_transacao": [
                "2026-08-01 10:00:00",
                "2026-08-01 11:00:00",
                "2026-08-01 12:00:00",
            ]
        }
    )

    with pytest.raises(
        ValueError,
        match="não possui registros suficientes",
    ):
        criar_folds_temporais(
            df,
            n_splits=3,
        )
