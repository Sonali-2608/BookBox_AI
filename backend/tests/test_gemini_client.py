import pytest

from app.ai import gemini_client


class FakeResponse:
    def __init__(self, text):
        self.text = text


class FakeModels:
    def __init__(self, response_text, raise_exc=None):
        self.response_text = response_text
        self.raise_exc = raise_exc
        self.calls = []

    def generate_content(self, model, contents, config=None):
        self.calls.append({"model": model, "contents": contents, "config": config})
        if self.raise_exc:
            raise self.raise_exc
        return FakeResponse(self.response_text)


class FakeClient:
    def __init__(self, response_text="hello", raise_exc=None):
        self.models = FakeModels(response_text, raise_exc)


@pytest.fixture(autouse=True)
def reset_client_singleton(monkeypatch):
    monkeypatch.setattr(gemini_client, "_client", None)
    yield
    monkeypatch.setattr(gemini_client, "_client", None)


def test_generate_content_returns_text(monkeypatch):
    monkeypatch.setattr(gemini_client.settings, "GEMINI_API_KEY", "fake-key")
    fake_client = FakeClient(response_text="The sky is blue.")
    monkeypatch.setattr(gemini_client, "_get_client", lambda: fake_client)

    result = gemini_client.generate_content("Why is the sky blue?")
    assert result == "The sky is blue."


def test_generate_content_passes_system_instruction(monkeypatch):
    monkeypatch.setattr(gemini_client.settings, "GEMINI_API_KEY", "fake-key")
    fake_client = FakeClient(response_text="ok")
    monkeypatch.setattr(gemini_client, "_get_client", lambda: fake_client)

    gemini_client.generate_content("hello", system_instruction="Be concise.")

    call = fake_client.models.calls[0]
    assert call["config"] is not None


def test_generate_content_uses_configured_model(monkeypatch):
    monkeypatch.setattr(gemini_client.settings, "GEMINI_API_KEY", "fake-key")
    monkeypatch.setattr(gemini_client.settings, "GEMINI_MODEL", "gemini-test-model")
    fake_client = FakeClient(response_text="ok")
    monkeypatch.setattr(gemini_client, "_get_client", lambda: fake_client)

    gemini_client.generate_content("hello")

    assert fake_client.models.calls[0]["model"] == "gemini-test-model"


def test_generate_content_raises_geminierror_when_no_api_key(monkeypatch):
    monkeypatch.setattr(gemini_client.settings, "GEMINI_API_KEY", None)

    with pytest.raises(gemini_client.GeminiError, match="not configured"):
        gemini_client.generate_content("hello")


def test_generate_content_wraps_sdk_exceptions(monkeypatch):
    monkeypatch.setattr(gemini_client.settings, "GEMINI_API_KEY", "fake-key")
    fake_client = FakeClient(raise_exc=RuntimeError("network exploded"))
    monkeypatch.setattr(gemini_client, "_get_client", lambda: fake_client)

    with pytest.raises(gemini_client.GeminiError, match="Gemini request failed"):
        gemini_client.generate_content("hello")


def test_generate_content_raises_on_empty_response(monkeypatch):
    monkeypatch.setattr(gemini_client.settings, "GEMINI_API_KEY", "fake-key")
    fake_client = FakeClient(response_text="")
    monkeypatch.setattr(gemini_client, "_get_client", lambda: fake_client)

    with pytest.raises(gemini_client.GeminiError, match="empty"):
        gemini_client.generate_content("hello")


def test_generate_json_parses_plain_json(monkeypatch):
    monkeypatch.setattr(
        gemini_client, "generate_content", lambda *a, **k: '{"reply": "hi", "book_ids": [1, 2]}'
    )
    result = gemini_client.generate_json("hello")
    assert result == {"reply": "hi", "book_ids": [1, 2]}


def test_generate_json_strips_markdown_fences(monkeypatch):
    monkeypatch.setattr(
        gemini_client,
        "generate_content",
        lambda *a, **k: '```json\n{"reply": "hi"}\n```',
    )
    result = gemini_client.generate_json("hello")
    assert result == {"reply": "hi"}


def test_generate_json_raises_on_invalid_json(monkeypatch):
    monkeypatch.setattr(gemini_client, "generate_content", lambda *a, **k: "not json at all")

    with pytest.raises(gemini_client.GeminiError, match="valid JSON"):
        gemini_client.generate_json("hello")
