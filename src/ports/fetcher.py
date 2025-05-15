from abc import ABC, abstractmethod
from datetime import datetime
from typing import AsyncIterator
from core.models import Feedback

class BaseFetcher(ABC):
    @abstractmethod
    async def fetch(
        self, since: datetime, until: datetime
    ) -> AsyncIterator[Feedback]:
        """Yield Feedback objects fetched in the [since, until) window."""
        ...
