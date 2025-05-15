# tests/adapters/test_playstore.py
import json
import os
from datetime import datetime, timedelta

import httpx
import pytest

from adapters.playstore import PlaystorePullAdapter
from config.settings import settings

TENANT = "tenant1"
TEST_APP_ID = "com.test.app"


@pytest.fixture(autouse=True)
def ensure_playstore_config(monkeypatch):
    pc = settings.PLATFORM_CONFIG.setdefault("playstore", {})
    apps = pc.setdefault("apps", {})
    api_keys = pc.setdefault("api_keys", {})
    monkeypatch.setitem(apps, TENANT, [TEST_APP_ID])
    monkeypatch.setitem(api_keys, TENANT, "fake-token")


@pytest.fixture
def mock_playstore_response():
    current_dir = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(current_dir, "mock_playstore_response.json")
    with open(path, "r") as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_fetch_success(mock_playstore_response, monkeypatch):
    async def mock_get(self, url, params=None, headers=None):
        class MockResponse:
            def __init__(self, data):
                self._data = data
                self.status_code = 200

            def json(self):
                return self._data

            def raise_for_status(self):
                pass

        return MockResponse(mock_playstore_response)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = PlaystorePullAdapter(TENANT, TEST_APP_ID)
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    reviews = mock_playstore_response["reviews"]
    assert len(feedbacks) == len(reviews)

    fb0 = feedbacks[0]
    first = reviews[0]
    assert fb0.external_id == first["reviewId"]
    assert fb0.metadata_["authorName"] == first["authorName"]
    assert fb0.tenant_id == TENANT
    assert fb0.source_instance == TEST_APP_ID


@pytest.mark.asyncio
async def test_fetch_failure(monkeypatch):
    async def mock_get(self, url, params=None, headers=None):
        class MockResponse:
            def __init__(self):
                self.status_code = 404

            def json(self):
                return None

            def raise_for_status(self):
                raise httpx.HTTPStatusError("Fail", request=None, response=self)

        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = PlaystorePullAdapter(TENANT, TEST_APP_ID)
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == 1
    fb = feedbacks[0]
    assert fb.external_id == "stub-1"
    assert "stub review" in fb.body.lower()
    assert fb.tenant_id == TENANT
    assert fb.source_instance == TEST_APP_ID


@pytest.mark.asyncio
async def test_fetch_empty_response(monkeypatch):
    async def mock_get(self, url, params=None, headers=None):
        class MockResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {"reviews": []}

            def raise_for_status(self):
                pass

        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = PlaystorePullAdapter(TENANT, TEST_APP_ID)
    since = datetime.utcnow() - timedelta(days=1)
    until = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert feedbacks == []
