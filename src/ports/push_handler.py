# src/ports/push_handler.py
from abc import ABC, abstractmethod

from core.models import Feedback


class BasePushHandler(ABC):
    """
    A push‐handler must implement handle(payload) to
    validate, normalize and return a single Feedback.
    """

    @abstractmethod
    async def handle(self, payload: dict) -> Feedback: ...
