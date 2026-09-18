from datetime import UTC, datetime

import pytest

from src.alerts.engine import criar_alerta
from src.evidence_context import build_evidence_context
from src.soc_assistant.assessment import (
    add_supported_hypothesis,
    build_guarded_assessment,
)


def test_guarded_assessment_preserva_identidade_e_lacunas_conhecidas():
    registro = {
        "id_transacao": 101,
        "cliente_pseudonimo": "cliente-01",
        "data_hora_transacao": datetime(2026, 8, 18, 12, 0, tzinfo=UTC),
        "tipo_transacao": "Pix",
        "valor_transacao": 5000.0,
        "proba_suspeita": 0.90,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.42,
        "score_risco_predito": 92.0,
        "falhas_login_recentes": 4,
        "dispositivo_novo_flag": True,
        "alteracao_limite_flag": False,
        "mudanca_localizacao_flag": False,
    }

    alerta = criar_alerta(
        registro,
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
        },
        alert_id="ALT-GUARDED-001",
        created_at=datetime(2026, 8, 18, 13, 0, tzinfo=UTC),
    )

    contexto = build_evidence_context(alerta)

    assessment = build_guarded_assessment(contexto)

    assert assessment.alert_id == contexto.alert_id
    assert assessment.missing_evidence == contexto.quality.missing_evidence


def test_guarded_assessment_inclui_apenas_evidencias_observadas_como_fatos():
    registro = {
        "id_transacao": 102,
        "cliente_pseudonimo": "cliente-02",
        "data_hora_transacao": datetime(2026, 8, 18, 14, 0, tzinfo=UTC),
        "tipo_transacao": "Pix",
        "valor_transacao": 7500.0,
        "proba_suspeita": 0.95,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.55,
        "score_risco_predito": 96.0,
        "falhas_login_recentes": 5,
        "dispositivo_novo_flag": True,
        "alteracao_limite_flag": True,
        "mudanca_localizacao_flag": True,
    }

    alerta = criar_alerta(
        registro,
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
        },
        alert_id="ALT-GUARDED-FACTS-001",
        created_at=datetime(2026, 8, 18, 14, 30, tzinfo=UTC),
    )

    contexto = build_evidence_context(alerta)

    assessment = build_guarded_assessment(contexto)

    assert tuple(fact.name for fact in assessment.facts) == (
        "failed_logins",
        "new_device",
    )


def test_guarded_assessment_preserva_valor_dos_fatos_observados():
    registro = {
        "id_transacao": 103,
        "cliente_pseudonimo": "cliente-03",
        "data_hora_transacao": datetime(2026, 8, 18, 15, 0, tzinfo=UTC),
        "tipo_transacao": "Pix",
        "valor_transacao": 8200.0,
        "proba_suspeita": 0.96,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.61,
        "score_risco_predito": 97.0,
        "falhas_login_recentes": 5,
        "dispositivo_novo_flag": False,
        "alteracao_limite_flag": True,
        "mudanca_localizacao_flag": True,
    }

    alerta = criar_alerta(
        registro,
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
        },
        alert_id="ALT-GUARDED-FACTS-002",
        created_at=datetime(2026, 8, 18, 15, 30, tzinfo=UTC),
    )

    contexto = build_evidence_context(alerta)

    assessment = build_guarded_assessment(contexto)

    assert assessment.facts[0].name == "failed_logins"
    assert assessment.facts[0].value == 5

    assert assessment.facts[1].name == "new_device"
    assert assessment.facts[1].value is False

    assert len(assessment.facts) == 2


def test_guarded_assessment_nao_promove_fatos_a_hipoteses_automaticamente():
    registro = {
        "id_transacao": 104,
        "cliente_pseudonimo": "cliente-04",
        "data_hora_transacao": datetime(2026, 8, 18, 16, 0, tzinfo=UTC),
        "tipo_transacao": "Pix",
        "valor_transacao": 9100.0,
        "proba_suspeita": 0.98,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.70,
        "score_risco_predito": 99.0,
        "falhas_login_recentes": 7,
        "dispositivo_novo_flag": True,
        "alteracao_limite_flag": True,
        "mudanca_localizacao_flag": True,
    }

    alerta = criar_alerta(
        registro,
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
            "alteracao_limite_flag",
            "mudanca_localizacao_flag",
        },
        alert_id="ALT-GUARDED-HYP-001",
        created_at=datetime(2026, 8, 18, 16, 30, tzinfo=UTC),
    )

    contexto = build_evidence_context(alerta)

    assessment = build_guarded_assessment(contexto)

    assert len(assessment.facts) == 4
    assert assessment.hypotheses == ()


def test_guarded_assessment_adiciona_hipotese_com_suporte_explicito():
    registro = {
        "id_transacao": 105,
        "cliente_pseudonimo": "cliente-05",
        "data_hora_transacao": datetime(2026, 8, 18, 17, 0, tzinfo=UTC),
        "tipo_transacao": "Pix",
        "valor_transacao": 9800.0,
        "proba_suspeita": 0.99,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.78,
        "score_risco_predito": 99.0,
        "falhas_login_recentes": 8,
        "dispositivo_novo_flag": True,
        "alteracao_limite_flag": False,
        "mudanca_localizacao_flag": False,
    }

    alerta = criar_alerta(
        registro,
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
        },
        alert_id="ALT-GUARDED-HYP-002",
        created_at=datetime(2026, 8, 18, 17, 30, tzinfo=UTC),
    )

    contexto = build_evidence_context(alerta)
    assessment = build_guarded_assessment(contexto)

    assessment = add_supported_hypothesis(
        assessment,
        statement="possible_account_compromise",
        supporting_fact_names=(
            "failed_logins",
            "new_device",
        ),
    )

    assert len(assessment.hypotheses) == 1
    assert assessment.hypotheses[0].statement == "possible_account_compromise"
    assert assessment.hypotheses[0].supporting_fact_names == (
        "failed_logins",
        "new_device",
    )


def test_guarded_assessment_rejeita_hipotese_com_fato_nao_observado():
    registro = {
        "id_transacao": 106,
        "cliente_pseudonimo": "cliente-06",
        "data_hora_transacao": datetime(2026, 8, 18, 18, 0, tzinfo=UTC),
        "tipo_transacao": "Pix",
        "valor_transacao": 8700.0,
        "proba_suspeita": 0.97,
        "anomalia_score": -1,
        "anomalia_score_bruto": -0.66,
        "score_risco_predito": 98.0,
        "falhas_login_recentes": 6,
        "dispositivo_novo_flag": True,
        "alteracao_limite_flag": False,
        "mudanca_localizacao_flag": True,
    }

    alerta = criar_alerta(
        registro,
        detector="isolation_forest",
        evidencias_observadas={
            "falhas_login_recentes",
            "dispositivo_novo_flag",
        },
        alert_id="ALT-GUARDED-HYP-003",
        created_at=datetime(2026, 8, 18, 18, 30, tzinfo=UTC),
    )

    contexto = build_evidence_context(alerta)
    assessment = build_guarded_assessment(contexto)

    with pytest.raises(
        ValueError,
        match="supporting facts must be observed",
    ):
        add_supported_hypothesis(
            assessment,
            statement="possible_location_anomaly",
            supporting_fact_names=(
                "failed_logins",
                "location_change",
            ),
        )

    assert assessment.hypotheses == ()
