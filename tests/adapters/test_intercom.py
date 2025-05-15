# tests/adapters/test_intercom.py
import json
import os
from datetime import datetime, timedelta

import httpx
import pytest
from pydantic import SecretStr
from utils.time_utils import utc_now
from adapters.intercom import IntercomPullAdapter
from config.settings import settings

TENANT = "tenant1"


@pytest.fixture(autouse=True)
def ensure_intercom_secret(monkeypatch):
    """
    Guarantee that settings.PLATFORM_CONFIG["intercom"]["secrets"]
    has an entry for TENANT.
    """
    monkeypatch.setitem(
        settings.PLATFORM_CONFIG["intercom"]["secrets"],
        TENANT,
        SecretStr("test_secret"),
    )


@pytest.fixture
def mock_intercom_response():
    path = os.path.join(os.path.dirname(__file__), "mock_intercom_response.json")
    with open(path) as f:
        return json.load(f)


@pytest.mark.asyncio
async def test_fetch_success(mock_intercom_response, monkeypatch):
    """Should yield one Feedback per conversation, tagged with the correct tenant."""

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

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = IntercomPullAdapter(TENANT)
    since = utc_now() - timedelta(days=1)
    until = utc_now()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == len(mock_intercom_response["conversations"])

    first = mock_intercom_response["conversations"][0]
    fb0 = feedbacks[0]
    assert fb0.external_id == first["id"]
    assert fb0.body == first["conversation_message"]["body"]
    # deep check one metadata field
    assert fb0.metadata_["user"]["name"] == first["user"]["name"]
    assert fb0.tenant_id == TENANT


@pytest.mark.asyncio
async def test_fetch_404_fallback(monkeypatch):
    """Should emit a single stub Feedback tagged with the tenant on any error."""

    async def mock_get(self, url, params=None, headers=None):
        class MockResponse:
            def __init__(self):
                self.status_code = 404

            def json(self):
                return {}

            def raise_for_status(self):
                raise httpx.HTTPStatusError("Not Found", request=None, response=self)

        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = IntercomPullAdapter(TENANT)
    since = utc_now() - timedelta(days=1)
    until = utc_now()

    feedbacks = [fb async for fb in adapter.fetch(since, until)]
    assert len(feedbacks) == 1

    fb = feedbacks[0]
    assert fb.external_id == "stub-intercom"
    assert "stub conversation" in fb.body.lower()
    assert fb.tenant_id == TENANT
