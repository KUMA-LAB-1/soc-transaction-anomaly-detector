import pandas as pd

from src.reporting.charts import (
    gerar_grafico_comparacao,
    gerar_grafico_detector,
    gerar_grafico_importancia_classificador,
)


def test_gerar_grafico_detector_cria_png(tmp_path):
    df = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "cliente-b", "cliente-c"],
            "hora": [10, 12, 3],
            "valor_transacao": [100.0, 200.0, 5000.0],
            "anomalia_modelo_teste": [1, 1, -1],
            "score_anomalia_modelo_teste": [0.8, 0.5, -0.9],
        }
    )

    gerar_grafico_detector(
        df=df,
        nome_modelo="modelo_teste",
        contamination=0.15,
        output_dir=tmp_path,
    )

    caminho = tmp_path / "anomalias_modelo_teste.png"

    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_gerar_grafico_detector_funciona_sem_anomalias(tmp_path):
    df = pd.DataFrame(
        {
            "cliente_pseudonimo": ["cliente-a", "cliente-b"],
            "hora": [10, 11],
            "valor_transacao": [100.0, 150.0],
            "anomalia_modelo_teste": [1, 1],
            "score_anomalia_modelo_teste": [0.8, 0.7],
        }
    )

    gerar_grafico_detector(
        df=df,
        nome_modelo="modelo_teste",
        contamination=0.15,
        output_dir=tmp_path,
    )

    caminho = tmp_path / "anomalias_modelo_teste.png"

    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_gerar_grafico_comparacao_cria_png(tmp_path):
    comparacao = pd.DataFrame(
        {
            "modelo": [
                "isolation_forest",
                "elliptic_envelope",
            ],
            "precision_vs_status_real": [0.8, 0.9],
            "recall_vs_status_real": [0.7, 0.8],
            "f1_vs_status_real": [0.75, 0.85],
        }
    )

    gerar_grafico_comparacao(
        comparacao=comparacao,
        output_dir=tmp_path,
    )

    caminho = tmp_path / "comparacao_detectores.png"

    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_gerar_grafico_importancia_cria_png(tmp_path):
    gerar_grafico_importancia_classificador(
        features=[
            "hora",
            "zscore_valor_cliente",
            "falhas_login_recentes",
        ],
        importancias=[0.2, 0.5, 0.3],
        auc=0.93,
        output_dir=tmp_path,
    )

    caminho = tmp_path / "importancia_features_classificador.png"

    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_gerar_grafico_importancia_aceita_auc_nan(tmp_path):
    gerar_grafico_importancia_classificador(
        features=[
            "hora",
            "valor_transacao",
        ],
        importancias=[0.4, 0.6],
        auc=float("nan"),
        output_dir=tmp_path,
    )

    caminho = tmp_path / "importancia_features_classificador.png"

    assert caminho.exists()
    assert caminho.stat().st_size > 0


def test_graficos_criam_diretorio_de_saida(tmp_path):
    output_dir = tmp_path / "reports" / "graficos"

    gerar_grafico_importancia_classificador(
        features=["hora"],
        importancias=[1.0],
        auc=0.90,
        output_dir=output_dir,
    )

    assert output_dir.exists()

    caminho = output_dir / "importancia_features_classificador.png"

    assert caminho.exists()
