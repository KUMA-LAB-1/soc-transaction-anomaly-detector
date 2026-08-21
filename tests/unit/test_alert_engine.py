from datetime import UTC, datetime

import pytest

from src.alerts.engine import (
    classificar_severidade,
    criar_alerta,
    deve_gerar_alerta,
)


def criar_registro(**overrides):
    registro = {
        "id_transacao": 101,
        "cliente_pseudonimo": "cliente-01",
        "data_hora_transacao": datetime(
            2026,
            8,
            18,
            12,
            0,
            tzinfo=UTC,
        ),
        "tipo_transacao": "Pix",
        "valor_transacao": 5000.0,
        "proba_suspeita": 0.90,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.42,
        "score_risco_predito": 92.0,
        "falhas_login_recentes": 4,
        "dispositivo_novo_flag": True,
        "alteracao_limite_flag": True,
        "mudanca_localizacao_flag": False,
    }

    registro.update(overrides)
    return registro


@pytest.mark.parametrize(
    ("score", "esperado"),
    [
        (0.0, "low"),
        (24.99, "low"),
        (25.0, "medium"),
        (49.99, "medium"),
        (50.0, "high"),
        (74.99, "high"),
        (75.0, "critical"),
        (100.0, "critical"),
    ],
)
def test_classificar_severidade(score, esperado):
    assert classificar_severidade(score) == esperado


@pytest.mark.parametrize("score", [-0.01, 100.01])
def test_classificar_severidade_rejeita_score_invalido(score):
    with pytest.raises(ValueError):
        classificar_severidade(score)


def test_deve_gerar_alerta_por_anomalia():
    registro = criar_registro(
        proba_suspeita=0.10,
        anomalia_score=-1,
    )

    assert deve_gerar_alerta(registro) is True


def test_deve_gerar_alerta_por_probabilidade():
    registro = criar_registro(
        proba_suspeita=0.50,
        anomalia_score=1,
    )

    assert deve_gerar_alerta(registro) is True


def test_nao_gera_alerta_sem_sinal_suficiente():
    registro = criar_registro(
        proba_suspeita=0.49,
        anomalia_score=1,
    )

    assert deve_gerar_alerta(registro) is False


def test_criar_alerta_normaliza_resultados_analiticos():
    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        alert_id="ALT-TESTE",
        created_at=datetime(
            2026,
            8,
            18,
            13,
            0,
            tzinfo=UTC,
        ),
    )

    assert alerta.alert_id == "ALT-TESTE"
    assert alerta.detection.anomaly_detected is True
    assert alerta.detection.suspicious_probability == 0.90
    assert alerta.detection.detector == "isolation_forest"
    assert alerta.risk.score == 92.0
    assert alerta.risk.severity == "critical"


def test_criar_alerta_preserva_contexto_da_transacao():
    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
    )

    assert alerta.event.transaction_id == 101
    assert alerta.event.customer_pseudonym == "cliente-01"
    assert alerta.event.transaction_type == "Pix"
    assert alerta.event.transaction_value == 5000.0


def test_criar_alerta_registra_evidencia_ausente():
    observadas = {
        "falhas_login_recentes",
        "dispositivo_novo_flag",
    }

    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        evidencias_observadas=observadas,
    )

    assert alerta.evidence.failed_logins.observed is True
    assert alerta.evidence.new_device.observed is True
    assert alerta.evidence.limit_change.observed is False
    assert alerta.evidence.location_change.observed is False

    assert alerta.quality.missing_evidence == (
        "alteracao_limite_flag",
        "mudanca_localizacao_flag",
    )


def test_criar_alerta_preserva_aviso_amostra_pequena():
    alerta = criar_alerta(
        criar_registro(),
        detector="isolation_forest",
        aviso_amostra_pequena=True,
    )

    assert alerta.quality.small_sample_warning is True


def test_criar_alerta_rejeita_registro_sem_criterio():
    registro = criar_registro(
        proba_suspeita=0.10,
        anomalia_score=1,
    )

    with pytest.raises(
        ValueError,
        match="não atende à política",
    ):
        criar_alerta(
            registro,
            detector="isolation_forest",
        )


def test_criar_alerta_adiciona_timezone_utc_em_timestamp_ingenuo():
    registro = criar_registro(
        data_hora_transacao=datetime(2026, 8, 18, 12, 0),
    )

    alerta = criar_alerta(
        registro,
        detector="isolation_forest",
    )

    assert alerta.event.transaction_timestamp.tzinfo == UTC


def test_criar_alerta_rejeita_created_at_sem_timezone():
    with pytest.raises(
        ValueError,
        match="created_at deve possuir timezone",
    ):
        criar_alerta(
            criar_registro(),
            detector="isolation_forest",
            created_at=datetime(2026, 8, 18, 13, 0),
        )


def test_criar_alerta_rejeita_registro_sem_cliente_pseudonimo():
    registro = criar_registro()
    registro.pop("cliente_pseudonimo")

    with pytest.raises(
        KeyError,
        match="cliente_pseudonimo",
    ):
        criar_alerta(
            registro,
            detector="isolation_forest",
        )
