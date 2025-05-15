# tests/adapters/test_twitter.py

import os
# ─── Set env vars BEFORE importing settings or adapter ─────────────
os.environ.setdefault("TWITTER_SEARCH_QUERY", "#feedback lang:en")
os.environ.setdefault("TWITTER_BEARER_TOKEN", "dummy_token")

import json
import pytest
import httpx
from datetime import datetime, timedelta

from adapters.twitter import TwitterPullAdapter
from core.models import Feedback

@pytest.fixture
def mock_twitter_response():
    path = os.path.join(os.path.dirname(__file__), "mock_twitter_response.json")
    with open(path, "r") as f:
        return json.load(f)

@pytest.mark.asyncio
async def test_fetch_success(mock_twitter_response, monkeypatch):
    """Adapter yields one Feedback per tweet in the mock JSON."""
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

    adapter = TwitterPullAdapter()
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == len(mock_twitter_response["data"])

    first = mock_twitter_response["data"][0]
    assert feedbacks[0].external_id == first["id"]
    assert feedbacks[0].body == first["text"]

@pytest.mark.asyncio
async def test_rate_limit_fallback(monkeypatch):
    """Adapter emits exactly one stub Feedback on HTTP 429."""
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

    adapter = TwitterPullAdapter()
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == 1
    fb = feedbacks[0]
    assert fb.external_id == "stub-twitter"
    assert "stub tweet" in fb.body.lower()
