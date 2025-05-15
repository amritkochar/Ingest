import os
import json
import pytest
import httpx
from datetime import datetime, timedelta
from pydantic import SecretStr

from adapters.intercom import IntercomPullAdapter
from core.models import Feedback
from config.settings import settings

@pytest.fixture(autouse=True)
def ensure_intercom_secret(monkeypatch):
    """
    Ensure settings.INTERCOM_SECRET is populated so the adapter __init__ won't fail.
    """
    # Inject a dummy SecretStr regardless of .env
    monkeypatch.setattr(settings, "INTERCOM_SECRET", SecretStr("test_secret"))

@pytest.fixture
def mock_intercom_response():
    path = os.path.join(os.path.dirname(__file__), "mock_intercom_response.json")
    with open(path, "r") as f:
        return json.load(f)

@pytest.mark.asyncio
async def test_fetch_success(mock_intercom_response, monkeypatch):
    """Should yield one Feedback per conversation in the JSON."""
    async def mock_get(self, url, params=None, headers=None):
        class MockResponse:
            def __init__(self, data):
                self._data = data
                self.status_code = 200
            def json(self):
                return self._data
            def raise_for_status(self):
                pass
        return MockResponse(mock_intercom_response)

    # Patch httpx.AsyncClient.get
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = IntercomPullAdapter()
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == len(mock_intercom_response["conversations"])

    first = mock_intercom_response["conversations"][0]
    assert feedbacks[0].external_id == first["id"]
    assert feedbacks[0].body == first["conversation_message"]["body"]
    assert feedbacks[0].metadata_["user"]["name"] == first["user"]["name"]

@pytest.mark.asyncio
async def test_fetch_404_fallback(monkeypatch):
    """Should emit a single stub Feedback on HTTP 404."""
    async def mock_get(self, url, params=None, headers=None):
        class MockResponse:
            def __init__(self):
                self.status_code = 404
            def json(self):
                return {}
            def raise_for_status(self):
                raise httpx.HTTPStatusError("Not Found", request=None, response=self)
        return MockResponse()

    # Patch httpx.AsyncClient.get
    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = IntercomPullAdapter()
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == 1
    fb = feedbacks[0]
    assert fb.external_id == "stub-intercom"
    assert "stub conversation" in fb.body.lower()
