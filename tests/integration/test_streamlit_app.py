from pathlib import Path

import requests
from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[2] / "streamlit_app.py"


def test_streamlit_app_renderiza_demo_sem_api_key(monkeypatch):
    import dotenv

    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)
    monkeypatch.setattr(
        dotenv,
        "load_dotenv",
        lambda *args, **kwargs: False,
    )

    app = AppTest.from_file(APP_PATH)
    app.run()

    assert not app.exception
    assert app.title[0].value == "KUMA GUARD"
    assert len(app.chat_input) == 1

    assert any("GEMINI_API_KEY" in warning.value for warning in app.warning)


def test_streamlit_app_carrega_configuracao_local_dotenv(monkeypatch):
    import dotenv

    calls = []

    def fake_load_dotenv(*args, **kwargs):
        calls.append(kwargs)
        monkeypatch.setenv(
            "GEMINI_API_KEY",
            "test-dotenv-key",
        )
        return True

    monkeypatch.delenv(
        "GEMINI_API_KEY",
        raising=False,
    )
    monkeypatch.delenv(
        "GEMINI_MODEL",
        raising=False,
    )
    monkeypatch.setattr(
        dotenv,
        "load_dotenv",
        fake_load_dotenv,
    )

    app = AppTest.from_file(APP_PATH)
    app.run()

    assert not app.exception
    assert calls == [{"override": False}]
    assert not any(
        "GEMINI_API_KEY" in warning.value
        for warning in app.warning
    )


def test_streamlit_app_envia_pergunta_ao_servico_sem_rede(
    monkeypatch,
):
    import json

    from src.genai.contracts import LlmResponse
    from src.genai.providers.gemini import GeminiLlmAdapter

    captured_requests = []

    def fake_generate(self, request):
        captured_requests.append(request)

        return LlmResponse(
            content="O incidente não está confirmado.",
        )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-streamlit-key",
    )
    monkeypatch.delenv(
        "GEMINI_MODEL",
        raising=False,
    )
    monkeypatch.setattr(
        GeminiLlmAdapter,
        "generate",
        fake_generate,
    )

    app = AppTest.from_file(APP_PATH)
    app.run()

    assert not app.exception
    assert len(app.chat_input) == 1

    app.chat_input[0].set_value("Este incidente está confirmado?").run()

    assert not app.exception
    assert len(captured_requests) == 1

    request = captured_requests[0]
    context = json.loads(request.context)

    assert request.user_message == ("Este incidente está confirmado?")
    assert context["alert_id"] == "ALT-DEMO-001"
    assert context["incident_confirmed"] is False

    assert len(app.chat_message) == 2
    assert app.chat_message[0].markdown[0].value == ("Este incidente está confirmado?")
    assert app.chat_message[1].markdown[0].value == ("O incidente não está confirmado.")



def test_streamlit_app_exibe_erro_especifico_quando_gemini_retorna_503(
    monkeypatch,
):
    from src.genai.providers.gemini import GeminiLlmAdapter

    response = requests.Response()
    response.status_code = 503

    def fake_generate(self, request):
        raise requests.HTTPError(
            "HTTP 503",
            response=response,
        )

    monkeypatch.setenv(
        "GEMINI_API_KEY",
        "test-streamlit-key",
    )
    monkeypatch.setattr(
        GeminiLlmAdapter,
        "generate",
        fake_generate,
    )

    app = AppTest.from_file(APP_PATH)
    app.run()

    assert not app.exception

    app.chat_input[0].set_value(
        "Quais fatos foram observados?"
    ).run()

    assert not app.exception
    assert len(app.chat_message) == 2

    assistant_message = app.chat_message[1]

    assert any(
        "503" in markdown.value
        and "temporariamente indisponível" in markdown.value.lower()
        for markdown in assistant_message.markdown
    )
