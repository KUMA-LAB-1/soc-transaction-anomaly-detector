from datetime import datetime, timedelta

import numpy as np
import pandas as pd
import pytest

from src.reporting import pdf_report
from src.security_detector import SecurityDetector


def criar_dataset_smoke(n_registros: int = 120) -> pd.DataFrame:
    rng = np.random.default_rng(42)
    inicio = datetime(2026, 1, 1, 8, 0)

    registros = []

    for i in range(n_registros):
        suspeita = i % 7 == 0

        registros.append(
            {
                "id_transacao": i + 1,
                "cliente_pseudonimo": f"cliente-{i % 15:02d}",
                "data_hora_transacao": inicio
                + timedelta(
                    hours=i * 3,
                ),
                "tipo_transacao": (
                    "Pix" if i % 3 == 0 else "Transferência" if i % 3 == 1 else "Compra"
                ),
                "status_transacao": (
                    "Bloqueada por Suspeita" if suspeita else "Aprovada"
                ),
                "valor_transacao": (
                    float(rng.uniform(3500, 8000))
                    if suspeita
                    else float(rng.uniform(20, 1200))
                ),
                "falhas_login_recentes": (
                    int(rng.integers(2, 6)) if suspeita else int(rng.integers(0, 2))
                ),
                "dispositivo_novo_flag": (suspeita and i % 2 == 0),
                "alteracao_limite_flag": (suspeita and i % 3 == 0),
                "mudanca_localizacao_flag": (suspeita and i % 5 == 0),
            }
        )

    return pd.DataFrame(registros)


@pytest.mark.integration
def test_pipeline_completo_smoke(
    monkeypatch,
    tmp_path,
):
    monkeypatch.chdir(tmp_path)

    (tmp_path / "reports" / "models").mkdir(
        parents=True,
        exist_ok=True,
    )

    detector = SecurityDetector(
        engine=object(),
    )

    dataset = criar_dataset_smoke()

    monkeypatch.setattr(
        detector.repository,
        "carregar_dataset_soc",
        lambda: dataset.copy(),
    )

    monkeypatch.setattr(
        pdf_report,
        "enriquecer_com_mitre",
        lambda **kwargs: {
            "mitre_id": "T1110",
            "tecnica": "Brute Force",
            "tatica": "Credential Access",
            "procedimentos": (
                "Procedimento de mitigação utilizado exclusivamente pelo smoke test."
            ),
            "fonte": "fake integration test",
            "criterio": "correlação sintética",
        },
    )

    detector.executar_pipeline_completo()

    assert detector.modelo_classificacao is not None
    assert detector.modelo_regressao is not None
    assert detector.modelo_agrupamento is not None

    assert detector.detector_operacional in {
        "isolation_forest",
        "local_outlier_factor",
        "one_class_svm",
        "elliptic_envelope",
    }

    assert "classificacao" in detector.metricas
    assert "regressao" in detector.metricas
    assert "comparacao_detectores" in detector.metricas

    assert (tmp_path / "reports" / "Relatorio_Incidente_SOC.pdf").exists()

    assert (tmp_path / "reports" / "historico_metricas.jsonl").exists()

    assert (tmp_path / "reports" / "comparacao_detectores.csv").exists()

    assert (tmp_path / "reports" / "comparacao_detectores.json").exists()

    assert (tmp_path / "reports" / "comparacao_detectores.png").exists()

    assert (tmp_path / "reports" / "importancia_features_classificador.png").exists()

    assert (tmp_path / "reports" / "models" / "classificador.joblib").exists()

    assert (tmp_path / "reports" / "models" / "regressao.joblib").exists()
