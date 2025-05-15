# tests/adapters/test_discourse.py
import json
import os
from datetime import datetime, timedelta

import httpx
import pytest

from adapters.discourse import DiscoursePullAdapter
from config.settings import settings

TENANT = "tenant1"


@pytest.fixture(autouse=True)
def ensure_base_url(monkeypatch):
    """
    Make sure settings.PLATFORM_CONFIG["discourse"]["base_urls"]
    contains our test tenant.
    """
    # inject a dummy Discourse URL for this tenant
    monkeypatch.setitem(
        settings.PLATFORM_CONFIG["discourse"]["base_urls"],
        TENANT,
        "https://discourse.example.com",
    )


@pytest.fixture
def mock_discourse_response():
    path = os.path.join(os.path.dirname(__file__), "mock_discourse_response.json")
    with open(path, "r") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_fetch_success(mock_discourse_response, monkeypatch):
    """Should yield one Feedback per topic with correct tenant tagging."""

    async def mock_get(self, url, params=None):
        class MockResponse:
            def __init__(self, data):
                self._data = data
                self.status_code = 200

            def json(self):
                return self._data

            def raise_for_status(self):
                pass

        return MockResponse(mock_discourse_response)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = DiscoursePullAdapter(TENANT)
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == len(mock_discourse_response["topics"])

    first = mock_discourse_response["topics"][0]
    fb0 = feedbacks[0]
    assert fb0.external_id == str(first["id"])
    assert fb0.body == first["title"]
    assert fb0.metadata_["posts_count"] == first["posts_count"]
    assert fb0.tenant_id == TENANT


@pytest.mark.asyncio
async def test_fetch_404_fallback(monkeypatch):
    """Should emit a single stub Feedback tagged with the tenant on any error."""

    async def mock_get(self, url, params=None):
        class MockResponse:
            def __init__(self):
                self.status_code = 404

            def json(self):
                return {}

            def raise_for_status(self):
                raise httpx.HTTPStatusError("Not Found", request=None, response=self)

        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = DiscoursePullAdapter(TENANT)
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == 1

    fb = feedbacks[0]
    assert fb.external_id == "stub-discourse"
    assert "stub topic" in fb.body.lower()
    assert fb.tenant_id == TENANT
