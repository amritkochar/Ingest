import json
import os

import pytest
from fastapi.testclient import TestClient
from pydantic import SecretStr

import app.main as app_module
from config.settings import settings

TENANT = "tenant1"


@pytest.fixture(autouse=True)
def set_dummy_secret(monkeypatch):
    """
    Ensure settings.PLATFORM_CONFIG['intercom']['secrets']
    contains our test tenant so handler __init__() won't fail.
    """
    intercom_cfg = settings.PLATFORM_CONFIG.setdefault("intercom", {})
    secrets = intercom_cfg.setdefault("secrets", {})
    monkeypatch.setitem(secrets, TENANT, SecretStr("dummy"))


client = TestClient(app_module.app)


def load_payload():
    path = os.path.join(os.path.dirname(__file__), "mock_intercom_push.json")
    with open(path) as f:
        return json.load(f)


def test_intercom_push_endpoint(monkeypatch):
    payload = load_payload()
    captured = {}

    async def fake_ingest(fb):
        captured["fb"] = fb
        return True

    # Patch the ingest function used in the FastAPI route
    monkeypatch.setattr(app_module, "ingest", fake_ingest)

    # POST to the webhook endpoint
    response = client.post(f"/webhook/intercom/{TENANT}", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["inserted"] is True

    # Validate captured Feedback
    fb = captured.get("fb")
    assert fb is not None
    assert fb.external_id == payload["data"]["item"]["id"]
    assert fb.source_type == "intercom"
    assert fb.source_instance == "push"
    assert fb.tenant_id == TENANT
    assert "New user message!" in fb.body
