import pandas as pd


def validar_e_preparar_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Preenche valores ausentes e remove registros duplicados."""
    if df.isnull().sum().sum() > 0:
        df = df.fillna(0)

    return df.drop_duplicates()
