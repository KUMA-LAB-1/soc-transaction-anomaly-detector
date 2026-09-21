from src.genai.evaluation_cases import build_generative_evaluation_cases

EXPECTED_CRITERIA = {
    "grounding",
    "non_hallucination",
    "authority_preservation",
    "coherence",
    "investigation_usefulness",
}


def test_catalogo_generativo_tem_cinco_casos_com_ids_unicos():
    cases = build_generative_evaluation_cases()

    assert len(cases) == 5

    case_ids = [case.case_id for case in cases]

    assert len(case_ids) == len(set(case_ids))
    assert case_ids == [
        "ALT-EVAL-001",
        "ALT-EVAL-002",
        "ALT-EVAL-003",
        "ALT-EVAL-004",
        "ALT-EVAL-005",
    ]


def test_catalogo_generativo_cobre_criterios_minimos():
    cases = build_generative_evaluation_cases()

    covered_criteria = {criterion for case in cases for criterion in case.criteria}

    assert EXPECTED_CRITERIA.issubset(covered_criteria)


def test_expectativas_generativas_sao_compativeis_com_o_contexto():
    cases = build_generative_evaluation_cases()

    for case in cases:
        fact_names = {fact.name for fact in case.assessment.facts}
        missing_evidence = set(case.assessment.missing_evidence)

        assert set(case.expected_fact_names).issubset(fact_names)

        assert set(case.expected_missing_evidence).issubset(missing_evidence)

        assert case.expected_incident_confirmed is case.assessment.incident_confirmed


def test_catalogo_inclui_caso_adversarial_sem_confirmacao_falsa():
    cases = build_generative_evaluation_cases()

    case = next(case for case in cases if case.case_id == "ALT-EVAL-003")

    assert "authority_preservation" in case.criteria
    assert case.expected_incident_confirmed is False
    assert case.assessment.incident_confirmed is False
    assert case.user_message


def test_catalogo_inclui_caso_de_nao_alucinacao():
    cases = build_generative_evaluation_cases()

    case = next(case for case in cases if case.case_id == "ALT-EVAL-002")

    assert "non_hallucination" in case.criteria

    assert set(case.forbidden_inventions) >= {
        "source_ip",
        "country",
    }

    assert {
        "source_ip",
        "country",
    }.issubset(set(case.assessment.missing_evidence))
