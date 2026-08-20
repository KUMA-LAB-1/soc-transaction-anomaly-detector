import pandas as pd

from .columns import COLUNA_CLIENTE_PADRAO


def validar_e_preparar_dataset(df: pd.DataFrame) -> pd.DataFrame:
    """Valida o contrato mínimo do dataset SOC e prepara os registros."""
    if COLUNA_CLIENTE_PADRAO not in df.columns:
        raise ValueError(
            "Dataset SOC inválido: coluna obrigatória "
            "'cliente_pseudonimo' ausente."
        )

    if df[COLUNA_CLIENTE_PADRAO].isna().any():
        raise ValueError(
            "Dataset SOC inválido: 'cliente_pseudonimo' "
            "não pode conter valores nulos."
        )

    pseudonimos = df[COLUNA_CLIENTE_PADRAO].astype(str).str.strip()

    if pseudonimos.eq("").any():
        raise ValueError(
            "Dataset SOC inválido: 'cliente_pseudonimo' "
            "não pode conter valores vazios."
        )

    if df.isnull().sum().sum() > 0:
        df = df.fillna(0)

    return df.drop_duplicates()
