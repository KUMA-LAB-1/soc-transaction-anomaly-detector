import json
from datetime import UTC, datetime

from src.alerts.contract import (
    Alert,
    AlertDetection,
    AlertEvent,
    AlertEvidence,
    AlertQuality,
    AlertRisk,
    EvidenceValue,
)
from src.alerts.jsonl_repository import JsonlAlertRepository


def criar_alerta(
    *,
    alert_id: str = "ALT-001",
    customer_pseudonym: str = "cliente-ç-01",
) -> Alert:
    return Alert(
        alert_id=alert_id,
        created_at=datetime(
            2026,
            8,
            18,
            15,
            30,
            tzinfo=UTC,
        ),
        event=AlertEvent(
            transaction_id=101,
            customer_pseudonym=customer_pseudonym,
            transaction_type="Pix",
            transaction_value=5000.0,
            transaction_timestamp=datetime(
                2026,
                8,
                18,
                15,
                0,
                tzinfo=UTC,
            ),
        ),
        detection=AlertDetection(
            suspicious_probability=0.91,
            anomaly_detected=True,
            anomaly_raw_score=-0.42,
            detector="isolation_forest",
        ),
        risk=AlertRisk(
            score=92.0,
            severity="critical",
        ),
        evidence=AlertEvidence(
            failed_logins=EvidenceValue(
                value=4,
                observed=True,
            ),
            new_device=EvidenceValue(
                value=True,
                observed=True,
            ),
            limit_change=EvidenceValue(
                value=False,
                observed=False,
            ),
            location_change=EvidenceValue(
                value=False,
                observed=True,
            ),
        ),
        quality=AlertQuality(
            small_sample_warning=False,
        ),
    )


def test_save_cria_arquivo_jsonl(tmp_path):
    caminho = tmp_path / "alerts.jsonl"
    repository = JsonlAlertRepository(caminho)

    repository.save(criar_alerta())

    assert caminho.exists()


def test_save_cria_diretorio_pai(tmp_path):
    caminho = tmp_path / "nested" / "soc" / "alerts.jsonl"
    repository = JsonlAlertRepository(caminho)

    repository.save(criar_alerta())

    assert caminho.exists()


def test_save_grava_json_valido(tmp_path):
    caminho = tmp_path / "alerts.jsonl"
    repository = JsonlAlertRepository(caminho)

    repository.save(criar_alerta())

    linha = caminho.read_text(
        encoding="utf-8",
    ).strip()

    dados = json.loads(linha)

    assert dados["alert_id"] == "ALT-001"
    assert dados["risk"]["severity"] == "critical"


def test_save_preserva_unicode(tmp_path):
    caminho = tmp_path / "alerts.jsonl"
    repository = JsonlAlertRepository(caminho)

    repository.save(
        criar_alerta(
            customer_pseudonym="cliente-ç-01",
        )
    )

    conteudo = caminho.read_text(
        encoding="utf-8",
    )

    assert "cliente-ç-01" in conteudo


def test_save_acrescenta_um_alerta_por_linha(tmp_path):
    caminho = tmp_path / "alerts.jsonl"
    repository = JsonlAlertRepository(caminho)

    repository.save(
        criar_alerta(
            alert_id="ALT-001",
        )
    )
    repository.save(
        criar_alerta(
            alert_id="ALT-002",
        )
    )

    linhas = caminho.read_text(
        encoding="utf-8",
    ).splitlines()

    assert len(linhas) == 2

    primeiro = json.loads(linhas[0])
    segundo = json.loads(linhas[1])

    assert primeiro["alert_id"] == "ALT-001"
    assert segundo["alert_id"] == "ALT-002"


def test_save_termina_registro_com_newline(tmp_path):
    caminho = tmp_path / "alerts.jsonl"
    repository = JsonlAlertRepository(caminho)

    repository.save(criar_alerta())

    conteudo = caminho.read_bytes()

    assert conteudo.endswith(b"\n")
