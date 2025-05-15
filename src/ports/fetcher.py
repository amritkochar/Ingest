# src/ports/fetcher.py
from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator

from core.models import Feedback

class BaseFetcher(ABC):
    """
    A pull‐adapter must implement fetch(since, until) and yield Feedback.
    """

    @abstractmethod
    async def fetch(
        self, since: datetime, until: datetime
    ) -> AsyncIterator[Feedback]:
        ...
