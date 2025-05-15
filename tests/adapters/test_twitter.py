import json
import os
from datetime import datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr

from adapters.twitter import TwitterPullAdapter
from config.settings import settings

TENANT = "tenant1"
TEST_QUERY = "#feedback1 lang:en"

@pytest.fixture(autouse=True)
def ensure_twitter_settings(monkeypatch):
    """
    Populate settings.TWITTER_BEARER_TOKENS and TWITTER_QUERIES
    for our test tenant so __init__ won't fail.
    """
    monkeypatch.setitem(settings.TWITTER_BEARER_TOKENS, TENANT, SecretStr("dummy_token"))
    monkeypatch.setitem(settings.TWITTER_QUERIES,     TENANT, TEST_QUERY)


@pytest.fixture
def mock_twitter_response():
    path = os.path.join(os.path.dirname(__file__), "mock_twitter_response.json")
    with open(path) as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_fetch_success(mock_twitter_response, monkeypatch):
    """Adapter yields one Feedback per tweet in the mock JSON, tagged with tenant."""
    async def mock_get(self, url, params=None, headers=None):
        class MockResponse:
            def __init__(self, payload):
                self._payload = payload
                self.status_code = 200
            def json(self):
                return self._payload
            def raise_for_status(self):
                pass
        return MockResponse(mock_twitter_response)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = TwitterPullAdapter(TENANT)
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    expected = mock_twitter_response["data"]
    assert len(feedbacks) == len(expected)

    first = expected[0]
    fb0 = feedbacks[0]
    assert fb0.external_id == first["id"]
    assert fb0.body == first["text"]
    assert fb0.tenant_id == TENANT


@pytest.mark.asyncio
async def test_rate_limit_fallback(monkeypatch):
    """Adapter emits exactly one stub Feedback on HTTP 429 or 401."""
    async def mock_get(self, url, params=None, headers=None):
        class MockResponse:
            def __init__(self):
                self.status_code = 429
            def json(self):
                return {}
            def raise_for_status(self):
                raise httpx.HTTPStatusError("Rate limited", request=None, response=self)
        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = TwitterPullAdapter(TENANT)
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == 1

    fb = feedbacks[0]
    assert fb.external_id == "stub-twitter"
    assert "stub tweet" in fb.body.lower()
    assert fb.tenant_id == TENANT
