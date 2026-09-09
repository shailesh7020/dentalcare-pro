from __future__ import annotations

from app.services.notifications.providers.base import (
    NotificationChannelProvider,
    ProviderDeliveryResult,
)


class InAppNotificationProvider(NotificationChannelProvider):
    async def send(
        self, recipient: str, title: str, message: str, data: dict | None = None
    ) -> ProviderDeliveryResult:
        # In-App notifications are stored in database and delivered via in-app feed
        return ProviderDeliveryResult(
            success=True,
            channel="IN_APP",
            recipient=recipient,
            message_id=f"inapp-{recipient}",
        )
