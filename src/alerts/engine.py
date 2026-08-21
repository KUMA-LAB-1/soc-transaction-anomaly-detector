from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, Collection, Mapping
from uuid import uuid4

from .contract import (
    Alert,
    AlertDetection,
    AlertEvent,
    AlertEvidence,
    AlertQuality,
    AlertRisk,
    EvidenceValue,
)

PROBABILIDADE_SUSPEITA_MINIMA = 0.50

LIMITE_MEDIUM = 25.0
LIMITE_HIGH = 50.0
LIMITE_CRITICAL = 75.0

EVIDENCE_FIELDS = {
    "falhas_login_recentes",
    "dispositivo_novo_flag",
    "alteracao_limite_flag",
    "mudanca_localizacao_flag",
}


def classificar_severidade(score: float) -> str:
    """Converte o score de risco de 0 a 100 em uma severidade operacional."""
    if not 0 <= score <= 100:
        raise ValueError("score de risco deve estar entre 0 e 100")

    if score >= LIMITE_CRITICAL:
        return "critical"

    if score >= LIMITE_HIGH:
        return "high"

    if score >= LIMITE_MEDIUM:
        return "medium"

    return "low"


def deve_gerar_alerta(registro: Mapping[str, Any]) -> bool:
    """Define se um registro analisado deve produzir um alerta SOC."""
    probabilidade = float(registro["proba_suspeita"])
    predicao_anomalia = int(registro["anomalia_score"])

    if not 0 <= probabilidade <= 1:
        raise ValueError("proba_suspeita deve estar entre 0 e 1")

    if predicao_anomalia not in {-1, 1}:
        raise ValueError("anomalia_score deve usar a convenção -1 ou 1")

    anomaly_detected = predicao_anomalia == -1

    return anomaly_detected or probabilidade >= PROBABILIDADE_SUSPEITA_MINIMA


def criar_alerta(
    registro: Mapping[str, Any],
    *,
    detector: str,
    aviso_amostra_pequena: bool = False,
    evidencias_observadas: Collection[str] | None = None,
    alert_id: str | None = None,
    created_at: datetime | None = None,
) -> Alert:
    """Transforma um registro analítico em um Alert estruturado."""
    if not deve_gerar_alerta(registro):
        raise ValueError("registro não atende à política de geração de alerta")

    score_risco = float(registro["score_risco_predito"])

    if not 0 <= score_risco <= 100:
        raise ValueError("score_risco_predito deve estar entre 0 e 100")

    evidencias_observadas_set = (
        set(evidencias_observadas)
        if evidencias_observadas is not None
        else set(EVIDENCE_FIELDS)
    )

    campos_ausentes = tuple(sorted(EVIDENCE_FIELDS - evidencias_observadas_set))

    transaction_timestamp = registro["data_hora_transacao"]

    if not isinstance(transaction_timestamp, datetime):
        raise TypeError("data_hora_transacao deve ser datetime")

    if transaction_timestamp.tzinfo is None:
        transaction_timestamp = transaction_timestamp.replace(tzinfo=UTC)

    created_at_final = created_at or datetime.now(UTC)

    if created_at_final.tzinfo is None:
        raise ValueError("created_at deve possuir timezone")

    return Alert(
        alert_id=alert_id or f"ALT-{uuid4()}",
        created_at=created_at_final,
        event=AlertEvent(
            transaction_id=registro.get("id_transacao"),
            customer_pseudonym=str(registro["cliente_pseudonimo"]),
            transaction_type=str(registro["tipo_transacao"]),
            transaction_value=float(registro["valor_transacao"]),
            transaction_timestamp=transaction_timestamp,
        ),
        detection=AlertDetection(
            suspicious_probability=float(registro["proba_suspeita"]),
            anomaly_detected=int(registro["anomalia_score"]) == -1,
            anomaly_raw_score=float(registro["anomalia_score_bruto"]),
            detector=detector,
        ),
        risk=AlertRisk(
            score=score_risco,
            severity=classificar_severidade(score_risco),
        ),
        evidence=AlertEvidence(
            failed_logins=EvidenceValue(
                value=int(registro.get("falhas_login_recentes", 0)),
                observed=("falhas_login_recentes" in evidencias_observadas_set),
            ),
            new_device=EvidenceValue(
                value=bool(registro.get("dispositivo_novo_flag", False)),
                observed=("dispositivo_novo_flag" in evidencias_observadas_set),
            ),
            limit_change=EvidenceValue(
                value=bool(registro.get("alteracao_limite_flag", False)),
                observed=("alteracao_limite_flag" in evidencias_observadas_set),
            ),
            location_change=EvidenceValue(
                value=bool(registro.get("mudanca_localizacao_flag", False)),
                observed=("mudanca_localizacao_flag" in evidencias_observadas_set),
            ),
        ),
        quality=AlertQuality(
            small_sample_warning=aviso_amostra_pequena,
            missing_evidence=campos_ausentes,
        ),
    )
