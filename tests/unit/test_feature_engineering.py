import pandas as pd

from src.features.engineering import criar_features


def test_features_historicas_nao_usam_eventos_futuros():
    df_passado = pd.DataFrame(
        {
            "cliente_pseudonimo": [
                "cliente-a",
                "cliente-b",
                "cliente-a",
            ],
            "valor_transacao": [
                100.0,
                200.0,
                120.0,
            ],
            "data_hora_transacao": [
                "2026-08-15 10:00:00",
                "2026-08-15 10:30:00",
                "2026-08-15 11:00:00",
            ],
        }
    )

    df_com_futuro = pd.concat(
        [
            df_passado,
            pd.DataFrame(
                {
                    "cliente_pseudonimo": ["cliente-b"],
                    "valor_transacao": [1_000_000.0],
                    "data_hora_transacao": [
                        "2026-08-15 12:00:00",
                    ],
                }
            ),
        ],
        ignore_index=True,
    )

    resultado_passado = criar_features(df_passado)
    resultado_com_futuro = criar_features(df_com_futuro)

    colunas_historicas = [
        "media_historica_cliente",
        "desvio_historico_cliente",
        "qtd_transacoes_anteriores",
        "zscore_valor_cliente",
    ]

    pd.testing.assert_frame_equal(
        resultado_passado[colunas_historicas].reset_index(drop=True),
        resultado_com_futuro[colunas_historicas]
        .iloc[: len(resultado_passado)]
        .reset_index(drop=True),
        check_dtype=False,
    )


def criar_dataset_base():
    return pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "cliente-a", "cliente-b"],
            "valor_transacao": [100.0, 200.0, 300.0],
            "data_hora_transacao": [
                "2026-08-15 10:00:00",
                "2026-08-15 11:00:00",
                "2026-08-15 12:00:00",
            ],
        }
    )


def test_criar_features_adiciona_colunas_esperadas():
    df = criar_dataset_base()

    resultado = criar_features(df)

    colunas_esperadas = {
        "media_historica_cliente",
        "desvio_historico_cliente",
        "qtd_transacoes_anteriores",
        "zscore_valor_cliente",
        "dia_semana",
        "falhas_login_recentes",
        "dispositivo_novo_flag",
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    }

    assert colunas_esperadas.issubset(resultado.columns)


def test_criar_features_conta_transacoes_anteriores_por_cliente():
    df = criar_dataset_base()

    resultado = criar_features(df)

    cliente_a = resultado[resultado["cliente_pseudonimo"] == "cliente-a"].reset_index(
        drop=True
    )

    assert cliente_a.loc[0, "qtd_transacoes_anteriores"] == 0
    assert cliente_a.loc[1, "qtd_transacoes_anteriores"] == 1


def test_media_historica_usa_apenas_transacoes_anteriores():
    df = criar_dataset_base()

    resultado = criar_features(df)

    cliente_a = resultado[resultado["cliente_pseudonimo"] == "cliente-a"].reset_index(
        drop=True
    )

    assert cliente_a.loc[1, "media_historica_cliente"] == 100.0


def test_criar_features_adiciona_sinais_de_seguranca_ausentes():
    df = criar_dataset_base()

    resultado = criar_features(df)

    assert (resultado["falhas_login_recentes"] == 0).all()
    assert not resultado["dispositivo_novo_flag"].any()
    assert not resultado["alteracao_limite_flag"].any()
    assert not resultado["mudanca_localizacao_flag"].any()


def test_criar_features_preserva_sinais_de_seguranca_existentes():
    df = criar_dataset_base()

    df["falhas_login_recentes"] = [3, 0, 1]
    df["dispositivo_novo_flag"] = [True, False, True]
    df["alteracao_limite_flag"] = [False, True, False]
    df["mudanca_localizacao_flag"] = [True, False, False]

    resultado = criar_features(df)

    assert resultado["falhas_login_recentes"].tolist() == [3, 0, 1]
    assert resultado["dispositivo_novo_flag"].tolist() == [True, False, True]
    assert resultado["alteracao_limite_flag"].tolist() == [False, True, False]
    assert resultado["mudanca_localizacao_flag"].tolist() == [True, False, False]


def test_criar_features_ordena_transacoes_cronologicamente():
    df = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "cliente-a"],
            "valor_transacao": [200.0, 100.0],
            "data_hora_transacao": [
                "2026-08-15 11:00:00",
                "2026-08-15 10:00:00",
            ],
        }
    )

    resultado = criar_features(df)

    assert resultado.iloc[0]["valor_transacao"] == 100.0
    assert resultado.iloc[1]["valor_transacao"] == 200.0
    assert resultado.iloc[1]["media_historica_cliente"] == 100.0
