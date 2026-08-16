import numpy as np
import pandas as pd

from src.data.validation import validar_e_preparar_dataset


def test_validar_dataset_preenche_nulos():
    df = pd.DataFrame(
        {
            "valor": [100.0, np.nan],
        }
    )

    resultado = validar_e_preparar_dataset(df)

    assert resultado["valor"].isnull().sum() == 0
    assert resultado.iloc[1]["valor"] == 0


def test_validar_dataset_remove_duplicados():
    df = pd.DataFrame(
        {
            "cliente": ["A", "A", "B"],
            "valor": [100, 100, 200],
        }
    )

    resultado = validar_e_preparar_dataset(df)

    assert len(resultado) == 2
