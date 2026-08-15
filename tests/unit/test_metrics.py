import json
from datetime import datetime

from src.reporting.metrics import salvar_historico_metricas


def test_salvar_historico_metricas_cria_arquivo(tmp_path):
    caminho = tmp_path / "historico.jsonl"

    resultado = salvar_historico_metricas(
        metricas={"classificacao": {"roc_auc_teste": 0.99}},
        aviso_amostra_pequena=False,
        caminho=caminho,
    )

    assert resultado == caminho
    assert caminho.exists()


def test_salvar_historico_metricas_grava_json_valido(tmp_path):
    caminho = tmp_path / "historico.jsonl"

    salvar_historico_metricas(
        metricas={
            "classificacao": {
                "roc_auc_teste": 0.99,
            }
        },
        aviso_amostra_pequena=False,
        caminho=caminho,
    )

    linha = caminho.read_text(encoding="utf-8").strip()

    registro = json.loads(linha)

    assert registro["amostra_pequena"] is False
    assert registro["classificacao"]["roc_auc_teste"] == 0.99
    assert "timestamp" in registro


def test_timestamp_eh_utc_com_timezone(tmp_path):
    caminho = tmp_path / "historico.jsonl"

    salvar_historico_metricas(
        metricas={},
        aviso_amostra_pequena=False,
        caminho=caminho,
    )

    registro = json.loads(caminho.read_text(encoding="utf-8").strip())

    timestamp = datetime.fromisoformat(registro["timestamp"])

    assert timestamp.tzinfo is not None
    assert timestamp.utcoffset().total_seconds() == 0


def test_salvar_historico_metricas_preserva_flag_amostra_pequena(
    tmp_path,
):
    caminho = tmp_path / "historico.jsonl"

    salvar_historico_metricas(
        metricas={},
        aviso_amostra_pequena=True,
        caminho=caminho,
    )

    registro = json.loads(caminho.read_text(encoding="utf-8").strip())

    assert registro["amostra_pequena"] is True


def test_salvar_historico_metricas_acrescenta_novas_linhas(
    tmp_path,
):
    caminho = tmp_path / "historico.jsonl"

    salvar_historico_metricas(
        metricas={"execucao": 1},
        aviso_amostra_pequena=False,
        caminho=caminho,
    )

    salvar_historico_metricas(
        metricas={"execucao": 2},
        aviso_amostra_pequena=False,
        caminho=caminho,
    )

    linhas = caminho.read_text(encoding="utf-8").splitlines()

    assert len(linhas) == 2

    primeiro = json.loads(linhas[0])
    segundo = json.loads(linhas[1])

    assert primeiro["execucao"] == 1
    assert segundo["execucao"] == 2


def test_salvar_metricas_cria_diretorio_pai(tmp_path):
    caminho = tmp_path / "reports" / "nested" / "historico.jsonl"

    salvar_historico_metricas(
        metricas={},
        aviso_amostra_pequena=False,
        caminho=caminho,
    )

    assert caminho.exists()
