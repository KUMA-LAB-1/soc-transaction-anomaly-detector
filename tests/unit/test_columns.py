import pandas as pd
import pytest

from src.data.columns import resolver_coluna_cliente


def test_resolver_coluna_cliente_canonica():
    df = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "cliente-b"],
            "valor_transacao": [100, 200],
        }
    )

    coluna = resolver_coluna_cliente(df)

    assert coluna == "cliente_pseudonimo"


def test_resolver_coluna_cliente_rejeita_dataset_sem_pseudonimo():
    df = pd.DataFrame(
        {
            "valor_transacao": [100, 200],
        }
    )

    with pytest.raises(
        ValueError,
        match="cliente_pseudonimo",
    ):
        resolver_coluna_cliente(df)
