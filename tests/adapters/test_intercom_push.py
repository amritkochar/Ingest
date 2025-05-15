# tests/adapters/test_intercom_push.py

import json
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

import app.main as app_module
from config.settings import settings


# 1. Ensure the app imports the dummy secret
@pytest.fixture(autouse=True)
def set_dummy_secret(monkeypatch):
    monkeypatch.setattr(settings, "INTERCOM_SECRET", SecretStr("dummy"))


# 2. TestClient against your FastAPI app
client = TestClient(app_module.app)


def load_payload():
    path = os.path.join(os.path.dirname(__file__), "mock_intercom_push.json")
    with open(path) as f:
        return json.load(f)


def test_intercom_push_endpoint(monkeypatch):
    payload = load_payload()
    captured = {}

    # 3. Define an async fake_ingest for FastAPI to await
    async def fake_ingest(fb):
        captured["fb"] = fb
        return True

    # 4. Monkey-patch the ingest function *in app.main*, not services
    monkeypatch.setattr(app_module, "ingest", fake_ingest)

    # 5. Exercise the HTTP endpoint
    response = client.post("/webhook/intercom/my-tenant", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["inserted"] is True

    # 6. Validate the captured Feedback
    fb = captured.get("fb")
    assert fb is not None
    assert fb.external_id == payload["data"]["item"]["id"]
    assert fb.source_type == "intercom"
    assert fb.source_instance == "push"
    assert fb.tenant_id == "my-tenant"
    assert "New user message!" in fb.body
