from __future__ import annotations

import os
from pathlib import Path

import dotenv
import requests
import streamlit as st

from src.genai.conversation import ConversationService
from src.genai.demo import build_demo_assessment
from src.genai.provider_runtime import (
    LlmProviderConfigurationError,
    create_llm_adapter,
    load_llm_provider_runtime_config,
)

st.set_page_config(
    page_title="KUMA GUARD",
    page_icon="\U0001f43b",
    layout="wide",
)

ENV_PATH = Path(__file__).resolve().parent / ".env"

dotenv.load_dotenv(
    dotenv_path=ENV_PATH,
    override=False,
)

assessment = build_demo_assessment()

st.title("KUMA GUARD")
st.caption(
    "Assistente GenAI para apoio à investigação e triagem defensiva de alertas SOC."
)

st.subheader("Estado factual da investigação")

alert_col, confirmation_col = st.columns(2)

with alert_col:
    st.metric(
        "Alert ID",
        assessment.alert_id,
    )

with confirmation_col:
    st.metric(
        "Incidente confirmado",
        "SIM" if assessment.incident_confirmed else "NÃO",
    )

with st.expander(
    "Fatos observados",
    expanded=True,
):
    for fact in assessment.facts:
        st.write(f"- `{fact.name}` = `{fact.value}`")

with st.expander(
    "Hipóteses suportadas",
    expanded=True,
):
    for hypothesis in assessment.hypotheses:
        supporting_facts = ", ".join(hypothesis.supporting_fact_names)

        st.write(f"- `{hypothesis.statement}` | suporte: `{supporting_facts}`")

with st.expander(
    "Evidências ausentes",
):
    for evidence_name in assessment.missing_evidence:
        st.write(f"- `{evidence_name}`")

with st.expander(
    "Verificações recomendadas",
):
    for check in assessment.recommended_checks:
        st.write(f"- `{check.action}` → `{check.evidence_name}`")

try:
    runtime_config = load_llm_provider_runtime_config(
        os.environ,
    )
except LlmProviderConfigurationError as exc:
    runtime_config = None
    st.warning(str(exc))

st.divider()
st.subheader("Conversa com o KUMA GUARD")

if runtime_config is not None:
    st.caption(
        f"Provider ativo: `{runtime_config.provider}` | "
        f"Modelo: `{runtime_config.model}`"
    )

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

user_message = st.chat_input(
    "Pergunte sobre o alerta...",
    disabled=runtime_config is None,
)

if user_message:
    st.session_state.messages.append(
        {
            "role": "user",
            "content": user_message,
        }
    )

    with st.chat_message("user"):
        st.markdown(user_message)

    adapter = create_llm_adapter(
        runtime_config,
    )
    service = ConversationService(
        adapter,
    )

    with st.chat_message("assistant"):
        with st.spinner("Analisando o contexto defensivo..."):
            try:
                response = service.ask(
                    assessment,
                    user_message=user_message,
                )
                assistant_message = response.content
                st.markdown(assistant_message)

            except requests.RequestException as exc:
                status_code = getattr(
                    getattr(
                        exc,
                        "response",
                        None,
                    ),
                    "status_code",
                    None,
                )

                if status_code == 503:
                    assistant_message = (
                        "Provider GenAI temporariamente "
                        "indisponível (HTTP 503). "
                        "As tentativas automáticas "
                        "foram esgotadas. "
                        "Tente novamente em alguns instantes."
                    )
                else:
                    assistant_message = (
                        "Não foi possível consultar "
                        "o provider GenAI. "
                        "Verifique se o runtime selecionado "
                        "está em execução "
                        "e tente novamente."
                    )

                st.error(assistant_message)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": assistant_message,
        }
    )
