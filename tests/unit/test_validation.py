import numpy as np
import pandas as pd
import pytest

from src.data.validation import validar_e_preparar_dataset


def criar_dataset_valido(**overrides):
    dados = {
        "cliente_pseudonimo": ["cliente-a", "cliente-b"],
        "valor": [100.0, 200.0],
    }

    dados.update(overrides)
    return pd.DataFrame(dados)


def test_validar_dataset_preenche_nulos():
    df = criar_dataset_valido(
        valor=[100.0, np.nan],
    )

    resultado = validar_e_preparar_dataset(df)

    assert resultado["valor"].isnull().sum() == 0
    assert resultado.iloc[1]["valor"] == 0


def test_validar_dataset_remove_duplicados():
    df = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "cliente-a", "cliente-b"],
            "valor": [100, 100, 200],
        }
    )

    resultado = validar_e_preparar_dataset(df)

    assert len(resultado) == 2


def test_validar_dataset_rejeita_cliente_pseudonimo_ausente():
    df = pd.DataFrame(
        {
            "valor": [100, 200],
        }
    )

    with pytest.raises(
        ValueError,
        match="cliente_pseudonimo",
    ):
        validar_e_preparar_dataset(df)


def test_validar_dataset_rejeita_cliente_pseudonimo_nulo():
    df = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", None],
            "valor": [100, 200],
        }
    )

    with pytest.raises(
        ValueError,
        match="não pode conter valores nulos",
    ):
        validar_e_preparar_dataset(df)


def test_validar_dataset_rejeita_cliente_pseudonimo_vazio():
    df = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "   "],
            "valor": [100, 200],
        }
    )

    with pytest.raises(
        ValueError,
        match="não pode conter valores vazios",
    ):
        validar_e_preparar_dataset(df)
