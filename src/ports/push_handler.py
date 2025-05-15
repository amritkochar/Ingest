from abc import ABC, abstractmethod
from typing import Dict

from core.models import Feedback


class BasePushHandler(ABC):
    @abstractmethod
    async def handle(self, payload: Dict) -> Feedback:
        """
        Normalize an incoming webhook payload into a Feedback object.
        """
        ...
