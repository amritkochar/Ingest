# tests/adapters/test_intercom_push.py

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
    Ensure settings.INTERCOM_SECRETS contains our test tenant
    so the handler __init__ won't fail.
    """
    # inject or override the dict entry
    monkeypatch.setitem(settings.INTERCOM_SECRETS, TENANT, SecretStr("dummy"))


client = TestClient(app_module.app)


def load_payload():
    path = os.path.join(os.path.dirname(__file__), "mock_intercom_push.json")
    with open(path) as f:
        return json.load(f)


def test_intercom_push_endpoint(monkeypatch):
    payload = load_payload()
    captured = {}

    # fake ingest coroutine
    async def fake_ingest(fb):
        captured["fb"] = fb
        return True

    # patch the ingest function used in the route
    monkeypatch.setattr(app_module, "ingest", fake_ingest)

    # post to the webhook, using our TENANT in the path
    response = client.post(f"/webhook/intercom/{TENANT}", json=payload)
    assert response.status_code == 200

    data = response.json()
    assert data["status"] == "ok"
    assert data["inserted"] is True

    # verify that the handler saw the correct tenant_id
    fb = captured.get("fb")
    assert fb is not None
    assert fb.external_id == payload["data"]["item"]["id"]
    assert fb.source_type == "intercom"
    assert fb.source_instance == "push"
    assert fb.tenant_id == TENANT
    assert "New user message!" in fb.body
