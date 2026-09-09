from __future__ import annotations

from abc import ABC, abstractmethod

from pydantic import BaseModel


class ProviderDeliveryResult(BaseModel):
    success: bool
    channel: str
    recipient: str
    message_id: str | None = None
    error: str | None = None


class NotificationChannelProvider(ABC):
    @abstractmethod
    async def send(
        self, recipient: str, title: str, message: str, data: dict | None = None
    ) -> ProviderDeliveryResult:
        pass
