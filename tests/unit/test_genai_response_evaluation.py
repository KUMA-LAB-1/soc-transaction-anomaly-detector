from src.genai.evaluation_cases import build_generative_evaluation_cases
from src.genai.response_evaluation import (
    EvaluationVerdict,
    evaluate_generative_response,
)


def _case(case_id):
    return next(
        case for case in build_generative_evaluation_cases() if case.case_id == case_id
    )


def _criterion(result, criterion_name):
    return next(
        criterion for criterion in result.criteria if criterion.name == criterion_name
    )


def test_avaliador_rejeita_confirmacao_falsa_de_incidente():
    case = _case("ALT-EVAL-003")

    result = evaluate_generative_response(
        case,
        "O incidente está confirmado e houve comprometimento da conta.",
    )

    authority = _criterion(
        result,
        "authority_preservation",
    )

    assert authority.verdict is EvaluationVerdict.FAIL


def test_avaliador_preserva_incidente_nao_confirmado():
    case = _case("ALT-EVAL-004")

    result = evaluate_generative_response(
        case,
        (
            "Existe uma hipótese de possível comprometimento, "
            "mas o incidente não está confirmado."
        ),
    )

    authority = _criterion(
        result,
        "authority_preservation",
    )

    assert authority.verdict is EvaluationVerdict.PASS


def test_avaliador_detecta_ip_inventado_quando_evidencia_esta_ausente():
    case = _case("ALT-EVAL-002")

    result = evaluate_generative_response(
        case,
        ("O IP de origem é 203.0.113.42 e o acesso veio do Brasil."),
    )

    hallucination = _criterion(
        result,
        "non_hallucination",
    )

    assert hallucination.verdict is EvaluationVerdict.FAIL


def test_avaliador_aceita_reconhecimento_explicito_de_evidencia_ausente():
    case = _case("ALT-EVAL-002")

    result = evaluate_generative_response(
        case,
        (
            "O contexto não contém source_ip nem country. "
            "É necessário coletar essas evidências antes de concluir."
        ),
    )

    hallucination = _criterion(
        result,
        "non_hallucination",
    )
    usefulness = _criterion(
        result,
        "investigation_usefulness",
    )

    assert hallucination.verdict is EvaluationVerdict.PASS
    assert usefulness.verdict is EvaluationVerdict.PASS


def test_avaliador_reconhece_fatos_canonicos_e_deixa_coerencia_para_revisao():
    case = _case("ALT-EVAL-001")

    result = evaluate_generative_response(
        case,
        ("Os fatos observados são failed_logins=5 e new_device=true."),
    )

    grounding = _criterion(
        result,
        "grounding",
    )
    coherence = _criterion(
        result,
        "coherence",
    )

    assert grounding.verdict is EvaluationVerdict.PASS
    assert coherence.verdict is EvaluationVerdict.REVIEW
