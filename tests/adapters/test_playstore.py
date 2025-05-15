import re
import pytest
import httpx
from datetime import datetime, timedelta
from adapters.playstore import PlaystorePullAdapter
from config.settings import settings
import json
import os

@pytest.fixture
def mock_playstore_response():
    # Load the mock response from the JSON file
    current_dir = os.path.dirname(os.path.abspath(__file__))
    file_path = os.path.join(current_dir, 'mock_playstore_response.json')
    with open(file_path, 'r') as f:
        mock_data = json.load(f)
    return mock_data

@pytest.mark.asyncio
async def test_fetch_success(mock_playstore_response, monkeypatch):
    """Test successful fetch from Play Store with mocked response."""
    
    async def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError("Request failed", request=None, response=self)
        
        return MockResponse(mock_playstore_response, 200)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = PlaystorePullAdapter()
    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(start_time, end_time)]

    assert len(feedbacks) == len(mock_playstore_response.get("reviews", []))
        
    # Basic validation of the first feedback item
    first_review = mock_playstore_response["reviews"][0]
    assert feedbacks[0].external_id == first_review["reviewId"]
    assert feedbacks[0].metadata_['authorName'] == first_review["authorName"]

@pytest.mark.asyncio
async def test_fetch_failure(monkeypatch):
    """Test handling of a failed fetch from Play Store (e.g., 404 error)."""
    
    async def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self, json_data, status_code):
                self.json_data = json_data
                self.status_code = status_code

            def json(self):
                return self.json_data

            def raise_for_status(self):
                if self.status_code >= 400:
                    raise httpx.HTTPStatusError("Request failed", request=None, response=self)
        
        return MockResponse(None, 404)

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = PlaystorePullAdapter()
    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(start_time, end_time)]
    
    # Expecting a single "stub" feedback due to the 404 error
    assert len(feedbacks) == 1
    assert feedbacks[0].body == "This is a stub review (404 fallback)"
    assert feedbacks[0].external_id == "stub-1"


@pytest.mark.asyncio
async def test_fetch_empty_response(monkeypatch):
    """Test handling of an empty reviews list from Play Store."""

    async def mock_get(*args, **kwargs):
        class MockResponse:
            def __init__(self):
                self.status_code = 200

            def json(self):
                return {"reviews": []}

            def raise_for_status(self):
                pass

        return MockResponse()

    monkeypatch.setattr(httpx.AsyncClient, "get", mock_get)

    adapter = PlaystorePullAdapter()
    start_time = datetime.utcnow() - timedelta(days=1)
    end_time = datetime.utcnow()

    feedbacks = [fb async for fb in adapter.fetch(start_time, end_time)]

    assert feedbacks == []
