import numpy as np
import pandas as pd
import pytest

from src.models.classification import treinar_classificador_triagem


def criar_dataset_classificacao() -> pd.DataFrame:
    registros = []

    for i in range(40):
        suspeita = i % 4 == 0

        registros.append(
            {
                "data_hora_transacao": (
                    pd.Timestamp("2026-01-01") + pd.Timedelta(hours=i)
                ),
                "tipo_transacao": "Pix" if i % 2 == 0 else "Transferência",
                "status_transacao": (
                    "Bloqueada por Suspeita" if suspeita else "Aprovada"
                ),
                "hora": i % 24,
                "media_historica_cliente": 100.0 + i,
                "desvio_historico_cliente": 10.0,
                "qtd_transacoes_anteriores": i,
                "zscore_valor_cliente": 3.0 if suspeita else 0.2,
                "dia_semana": i % 7,
                "falhas_login_recentes": 3 if suspeita else 0,
                "dispositivo_novo_flag": suspeita,
                "alteracao_limite_flag": suspeita,
                "mudanca_localizacao_flag": False,
            }
        )

    return pd.DataFrame(registros)


def test_treinar_classificador_retorna_modelo_e_metricas():
    df = criar_dataset_classificacao()

    resultado = treinar_classificador_triagem(df)

    assert resultado["modelo"] is not None
    assert resultado["classes_no_treino"] == 2

    metricas = resultado["metricas"]

    assert metricas["n_treino"] == 30
    assert metricas["n_teste"] == 10
    assert metricas["classes_no_treino"] == 2
    assert len(metricas["matriz_confusao"]) == 2
    assert len(metricas["matriz_confusao"][0]) == 2


def test_probabilidades_tem_mesmo_tamanho_do_dataset():
    df = criar_dataset_classificacao()

    resultado = treinar_classificador_triagem(df)

    probabilidades = resultado["proba_suspeita"]

    assert len(probabilidades) == len(df)


def test_probabilidades_ficam_entre_zero_e_um():
    df = criar_dataset_classificacao()

    resultado = treinar_classificador_triagem(df)

    probabilidades = resultado["proba_suspeita"]

    assert np.all(probabilidades >= 0)
    assert np.all(probabilidades <= 1)


def test_retorna_features_e_importancias_consistentes():
    df = criar_dataset_classificacao()

    resultado = treinar_classificador_triagem(df)

    assert len(resultado["features"]) > 0
    assert len(resultado["features"]) == len(resultado["importancias"])

    assert "hora" in resultado["features"]
    assert "zscore_valor_cliente" in resultado["features"]
    assert "falhas_login_recentes" in resultado["features"]

    assert any(
        feature.startswith("tipo_transacao_") for feature in resultado["features"]
    )


def test_dataset_com_classe_unica_nao_quebra():
    df = criar_dataset_classificacao()
    df["status_transacao"] = "Aprovada"

    resultado = treinar_classificador_triagem(df)

    assert resultado["classes_no_treino"] == 1
    assert np.isnan(resultado["metricas"]["roc_auc_teste"])
    assert resultado["metricas"]["roc_auc_cv_media"] is None

    assert np.all(resultado["proba_suspeita"] == 0.0)


def test_dataset_totalmente_suspeito_retorna_probabilidade_constante():
    df = criar_dataset_classificacao()
    df["status_transacao"] = "Bloqueada por Suspeita"

    resultado = treinar_classificador_triagem(df)

    assert resultado["classes_no_treino"] == 1
    assert np.all(resultado["proba_suspeita"] == 1.0)


def test_classificador_mantem_validacao_random_por_padrao():
    df = criar_dataset_classificacao()

    resultado = treinar_classificador_triagem(df)

    assert resultado["metricas"]["estrategia_validacao"] == "random"


def test_classificador_suporta_validacao_temporal():
    df = criar_dataset_classificacao()

    resultado = treinar_classificador_triagem(
        df,
        estrategia_validacao="temporal",
    )

    metricas = resultado["metricas"]

    assert metricas["estrategia_validacao"] == "temporal"
    assert metricas["n_treino"] == 30
    assert metricas["n_teste"] == 10


def test_classificador_temporal_produz_cv_temporal():
    df = criar_dataset_classificacao()

    resultado = treinar_classificador_triagem(
        df,
        estrategia_validacao="temporal",
    )

    assert len(resultado["cv_scores"]) > 0


def test_classificador_rejeita_estrategia_desconhecida():
    df = criar_dataset_classificacao()

    with pytest.raises(
        ValueError,
        match="estrategia_validacao",
    ):
        treinar_classificador_triagem(
            df,
            estrategia_validacao="telepatica",
        )
