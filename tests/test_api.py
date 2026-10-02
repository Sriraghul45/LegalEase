from fastapi.testclient import TestClient

from backend.ai_core.gemini_generator import GeminiDocumentGenerator, GeminiGenerationError
from backend.main import app
from backend.api import routes


class FakeGenerator:
    def __init__(self):
        pass

    def generate_document(self, document_type, parties, terms, effective_date):
        return (
            f"DRAFT - FOR REVIEW\n\n{document_type}\n\n"
            f"Parties: {parties}\nTerms: {terms}\nEffective: {effective_date}"
        )


def test_root():
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_generate_with_mocked_ai(monkeypatch):
    monkeypatch.setattr(routes, "GeminiDocumentGenerator", FakeGenerator)
    client = TestClient(app)
    response = client.post(
        "/generate",
        json={
            "document_type": "NDA",
            "parties": "Alice, Bob",
            "terms": "Keep information confidential",
            "effective_date": "October 2, 2026",
        },
    )
    assert response.status_code == 200
    assert response.json()["document_type"] == "NDA"
    assert "Alice" in response.json()["content"]


def test_generate_validates_empty_fields():
    client = TestClient(app)
    response = client.post(
        "/generate",
        json={
            "document_type": "",
            "parties": "Alice",
            "terms": "Confidential",
            "effective_date": "Today",
        },
    )
    assert response.status_code == 422


def test_generate_retries_on_transient_503(monkeypatch):
    class FakeResponse:
        text = "Generated draft body"

    class FakeClient:
        def __init__(self):
            self.calls = 0

        class models:
            @staticmethod
            def generate_content(*args, **kwargs):
                return None

    fake_client = FakeClient()

    def fake_generate_content(*args, **kwargs):
        fake_client.calls += 1
        if fake_client.calls < 3:
            raise RuntimeError("503 UNAVAILABLE: model is busy")
        return FakeResponse()

    fake_client.models.generate_content = fake_generate_content

    generator = GeminiDocumentGenerator(api_key="test-key")
    generator.client = fake_client
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    result = generator.generate_document(
        document_type="NDA",
        parties="Alice and Bob",
        terms="Confidentiality",
        effective_date="2026-10-02",
    )

    assert result == "Generated draft body"
    assert fake_client.calls == 3


def test_generate_raises_user_friendly_error_after_retries(monkeypatch):
    class FakeClient:
        class models:
            @staticmethod
            def generate_content(*args, **kwargs):
                raise RuntimeError("503 UNAVAILABLE: high demand")

    generator = GeminiDocumentGenerator(api_key="test-key")
    generator.client = FakeClient()
    monkeypatch.setattr("time.sleep", lambda *_args, **_kwargs: None)

    try:
        generator.generate_document(
            document_type="NDA",
            parties="Alice and Bob",
            terms="Confidentiality",
            effective_date="2026-10-02",
        )
        assert False, "Expected GeminiGenerationError"
    except GeminiGenerationError as exc:
        message = str(exc)
        assert "temporarily busy" in message.lower()
        assert "try again" in message.lower()
