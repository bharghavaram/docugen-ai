"""Tests for DocuGen AI API."""
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient


def get_mock_service():
    svc = MagicMock()
    svc.generate_document.return_value = {
        "doc_type": "executive_summary",
        "content": "Generated document content",
        "provider": "claude",
        "status": "success",
    }
    svc.summarise.return_value = {
        "summary": "This is a test summary.",
        "style": "concise",
        "status": "success",
    }
    svc.list_templates.return_value = [
        "executive_summary", "technical_report", "business_proposal", "meeting_notes"
    ]
    return svc


@pytest.fixture
def client():
    from app.services.docgen_service import get_docgen_service
    from main import app
    app.dependency_overrides[get_docgen_service] = get_mock_service
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


def test_root(client):
    resp = client.get("/")
    assert resp.status_code == 200
    data = resp.json()
    assert "service" in data


def test_generate_invalid_doc_type(client):
    resp = client.post("/api/v1/documents/generate", json={
        "query": "Write a report about sales",
        "doc_type": "invalid_type",
    })
    assert resp.status_code == 400


def test_generate_invalid_provider(client):
    resp = client.post("/api/v1/documents/generate", json={
        "query": "Write a report",
        "doc_type": "executive_summary",
        "llm_provider": "gpt4",
    })
    assert resp.status_code == 400


def test_generate_valid(client):
    resp = client.post("/api/v1/documents/generate", json={
        "query": "Write a report about quarterly sales",
        "doc_type": "executive_summary",
        "llm_provider": "claude",
    })
    assert resp.status_code == 200


def test_summarise_too_short(client):
    resp = client.post("/api/v1/documents/summarise", json={
        "text": "Short text",
        "style": "concise",
    })
    assert resp.status_code == 400


def test_summarise_valid(client):
    long_text = "This is a sufficiently long piece of text that should be summarised. " * 5
    resp = client.post("/api/v1/documents/summarise", json={
        "text": long_text,
        "style": "concise",
    })
    assert resp.status_code == 200
