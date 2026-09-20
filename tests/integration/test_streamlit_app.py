from pathlib import Path

from streamlit.testing.v1 import AppTest

APP_PATH = Path(__file__).resolve().parents[2] / "streamlit_app.py"


def test_streamlit_app_renderiza_demo_sem_api_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GEMINI_MODEL", raising=False)

    app = AppTest.from_file(APP_PATH)
    app.run()

    assert not app.exception
    assert app.title[0].value == "KUMA GUARD"
    assert len(app.chat_input) == 1

    assert any("GEMINI_API_KEY" in warning.value for warning in app.warning)


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
