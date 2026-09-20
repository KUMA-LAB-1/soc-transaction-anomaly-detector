from src.genai.demo import build_demo_assessment


def test_demo_assessment_tem_estado_defensivo_estavel():
    assessment = build_demo_assessment()

    assert assessment.alert_id == "ALT-DEMO-001"
    assert assessment.incident_confirmed is False
    assert assessment.missing_evidence == ("location_change",)


def test_demo_assessment_expoe_fatos_observados():
    assessment = build_demo_assessment()

    assert [(fact.name, fact.value) for fact in assessment.facts] == [
        ("failed_logins", 5),
        ("new_device", True),
    ]


def test_demo_assessment_mantem_comprometimento_como_hipotese():
    assessment = build_demo_assessment()

    assert len(assessment.hypotheses) == 1

    hypothesis = assessment.hypotheses[0]

    assert hypothesis.statement == "possible_account_compromise"
    assert hypothesis.supporting_fact_names == (
        "failed_logins",
        "new_device",
    )


def test_demo_assessment_recomenda_coleta_da_evidencia_ausente():
    assessment = build_demo_assessment()

    assert len(assessment.recommended_checks) == 1

    check = assessment.recommended_checks[0]

    assert check.action == "collect_missing_evidence"
    assert check.evidence_name == "location_change"
