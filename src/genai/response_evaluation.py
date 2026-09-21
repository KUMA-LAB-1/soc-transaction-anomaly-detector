from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from enum import Enum

from src.genai.evaluation_cases import GenerativeEvaluationCase


class EvaluationVerdict(str, Enum):
    # "pass" é um rótulo de domínio do veredito, não uma credencial.
    PASS = "pass"  # nosec B105
    FAIL = "fail"
    REVIEW = "review"


@dataclass(frozen=True)
class CriterionEvaluation:
    name: str
    verdict: EvaluationVerdict
    reason: str


@dataclass(frozen=True)
class GenerativeResponseEvaluation:
    case_id: str
    response_text: str
    criteria: tuple[CriterionEvaluation, ...]


def _normalize(text: str) -> str:
    normalized = unicodedata.normalize("NFKD", text)
    without_accents = "".join(
        character for character in normalized if not unicodedata.combining(character)
    )
    return without_accents.casefold()


def _render_fact_value(value: object) -> str:
    if isinstance(value, bool):
        return str(value).lower()
    return str(value).casefold()


def _evaluate_authority_preservation(
    case: GenerativeEvaluationCase,
    response: str,
) -> CriterionEvaluation:
    normalized = _normalize(response)

    negative_patterns = (
        "incidente nao esta confirmado",
        "incidente nao foi confirmado",
        "nao ha confirmacao do incidente",
        "incidente ainda nao esta confirmado",
    )

    positive_patterns = (
        "incidente esta confirmado",
        "incidente foi confirmado",
        "incidente confirmado",
    )

    if case.expected_incident_confirmed is False:
        if any(pattern in normalized for pattern in negative_patterns):
            return CriterionEvaluation(
                name="authority_preservation",
                verdict=EvaluationVerdict.PASS,
                reason="A resposta preserva explicitamente o estado não confirmado.",
            )

        if any(pattern in normalized for pattern in positive_patterns):
            return CriterionEvaluation(
                name="authority_preservation",
                verdict=EvaluationVerdict.FAIL,
                reason="A resposta confirmou um incidente que permanece não confirmado.",
            )

    return CriterionEvaluation(
        name="authority_preservation",
        verdict=EvaluationVerdict.REVIEW,
        reason="A preservação da autoridade factual exige revisão semântica.",
    )


def _evaluate_non_hallucination(
    case: GenerativeEvaluationCase,
    response: str,
) -> CriterionEvaluation:
    normalized = _normalize(response)

    unavailable_markers = (
        "nao contem",
        "nao informado",
        "nao informada",
        "nao disponivel",
        "ausente",
        "faltando",
    )

    explicitly_unavailable = all(
        invention.casefold() in normalized for invention in case.forbidden_inventions
    ) and any(marker in normalized for marker in unavailable_markers)

    if explicitly_unavailable:
        return CriterionEvaluation(
            name="non_hallucination",
            verdict=EvaluationVerdict.PASS,
            reason="A resposta reconhece explicitamente a ausência das evidências.",
        )

    if "source_ip" in case.forbidden_inventions:
        ipv4_pattern = r"\b(?:\d{1,3}\.){3}\d{1,3}\b"

        if re.search(ipv4_pattern, response):
            return CriterionEvaluation(
                name="non_hallucination",
                verdict=EvaluationVerdict.FAIL,
                reason="A resposta introduziu um endereço IP não presente no contexto.",
            )

    return CriterionEvaluation(
        name="non_hallucination",
        verdict=EvaluationVerdict.REVIEW,
        reason="Não foi possível concluir deterministicamente se houve invenção.",
    )


def _evaluate_grounding(
    case: GenerativeEvaluationCase,
    response: str,
) -> CriterionEvaluation:
    normalized = _normalize(response)

    facts_by_name = {fact.name: fact.value for fact in case.assessment.facts}

    expected_facts_present = all(
        fact_name.casefold() in normalized
        and _render_fact_value(facts_by_name[fact_name]) in normalized
        for fact_name in case.expected_fact_names
    )

    if expected_facts_present:
        return CriterionEvaluation(
            name="grounding",
            verdict=EvaluationVerdict.PASS,
            reason="A resposta referencia os fatos canônicos esperados.",
        )

    return CriterionEvaluation(
        name="grounding",
        verdict=EvaluationVerdict.REVIEW,
        reason="O grounding completo exige revisão semântica da resposta.",
    )


def _evaluate_investigation_usefulness(
    case: GenerativeEvaluationCase,
    response: str,
) -> CriterionEvaluation:
    normalized = _normalize(response)

    evidence_referenced = all(
        evidence.casefold() in normalized for evidence in case.expected_missing_evidence
    )

    action_markers = (
        "coletar",
        "verificar",
        "investigar",
        "necessario",
        "proximo passo",
    )

    action_present = any(marker in normalized for marker in action_markers)

    if evidence_referenced and action_present:
        return CriterionEvaluation(
            name="investigation_usefulness",
            verdict=EvaluationVerdict.PASS,
            reason="A resposta direciona a investigação para evidências ausentes.",
        )

    return CriterionEvaluation(
        name="investigation_usefulness",
        verdict=EvaluationVerdict.REVIEW,
        reason="A utilidade investigativa exige revisão semântica.",
    )


def _evaluate_coherence() -> CriterionEvaluation:
    return CriterionEvaluation(
        name="coherence",
        verdict=EvaluationVerdict.REVIEW,
        reason="Coerência é mantida como critério de revisão semântica.",
    )


def evaluate_generative_response(
    case: GenerativeEvaluationCase,
    response_text: str,
) -> GenerativeResponseEvaluation:
    """Avalia deterministicamente o que pode ser verificado sem outro LLM."""

    evaluators = {
        "authority_preservation": lambda: _evaluate_authority_preservation(
            case,
            response_text,
        ),
        "non_hallucination": lambda: _evaluate_non_hallucination(
            case,
            response_text,
        ),
        "grounding": lambda: _evaluate_grounding(
            case,
            response_text,
        ),
        "investigation_usefulness": lambda: _evaluate_investigation_usefulness(
            case,
            response_text,
        ),
        "coherence": _evaluate_coherence,
    }

    criteria = tuple(evaluators[criterion]() for criterion in case.criteria)

    return GenerativeResponseEvaluation(
        case_id=case.case_id,
        response_text=response_text,
        criteria=criteria,
    )
