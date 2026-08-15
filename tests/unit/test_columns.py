import pandas as pd

from src.data.columns import resolver_coluna_cliente


def test_resolver_coluna_cliente_existente():
    df = pd.DataFrame(
        {
            "cliente_anonimizado": ["cliente-a", "cliente-b"],
            "valor_transacao": [100, 200],
        }
    )

    coluna = resolver_coluna_cliente(df)

    assert coluna == "cliente_anonimizado"


def test_resolver_coluna_cliente_cria_fallback():
    df = pd.DataFrame(
        {
            "valor_transacao": [100, 200],
        }
    )

    coluna = resolver_coluna_cliente(df)

    assert coluna == "cliente_pseudonimo"
    assert "cliente_pseudonimo" in df.columns
    assert (df["cliente_pseudonimo"] == "Usuário Anonimizado").all()
