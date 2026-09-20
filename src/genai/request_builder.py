from __future__ import annotations

import json

from src.soc_assistant.assessment import GuardedSocAssessment

from .contracts import LlmRequest

PUBLIC_SYSTEM_PROMPT = """Você é o KUMA GUARD, um assistente de apoio à triagem SOC.

Use somente as informações presentes no contexto fornecido.

Diferencie fatos observados, evidências ausentes e hipóteses.
Não invente informações que não estejam presentes no contexto.
Não transforme uma anomalia, hipótese ou score em confirmação de incidente.
Se o incidente não estiver confirmado no contexto, não o apresente como confirmado.
Quando faltarem evidências, indique a necessidade de investigação adicional.
Responda de forma técnica, clara e objetiva.
"""


def build_llm_request(
    assessment: GuardedSocAssessment,
    *,
    user_message: str,
) -> LlmRequest:
    """Projeta o assessment defensivo em uma requisição para o LLM."""

    context = {
        "alert_id": assessment.alert_id,
        "facts": [
            {
                "name": fact.name,
                "value": fact.value,
            }
            for fact in assessment.facts
        ],
        "hypotheses": [
            {
                "statement": hypothesis.statement,
                "supporting_fact_names": list(hypothesis.supporting_fact_names),
            }
            for hypothesis in assessment.hypotheses
        ],
        "incident_confirmed": assessment.incident_confirmed,
        "missing_evidence": list(assessment.missing_evidence),
        "recommended_checks": [
            {
                "action": check.action,
                "evidence_name": check.evidence_name,
            }
            for check in assessment.recommended_checks
        ],
    }

    return LlmRequest(
        system_prompt=PUBLIC_SYSTEM_PROMPT,
        context=json.dumps(
            context,
            ensure_ascii=False,
            sort_keys=True,
        ),
        user_message=user_message,
    )
