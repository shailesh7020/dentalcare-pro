from __future__ import annotations

import logging
from uuid import uuid4

from app.services.notifications.providers.base import (
    NotificationChannelProvider,
    ProviderDeliveryResult,
)

logger = logging.getLogger("notifications.email")


class EmailNotificationProvider(NotificationChannelProvider):
    def __init__(self, sender_email: str = "notifications@dentalcarepro.com"):
        self.sender_email = sender_email

    async def send(
        self, recipient: str, title: str, message: str, data: dict | None = None
    ) -> ProviderDeliveryResult:
        if not recipient or "@" not in recipient:
            return ProviderDeliveryResult(
                success=False,
                channel="EMAIL",
                recipient=recipient,
                error="Invalid email address",
            )

        logger.info(
            "Dispatching EMAIL to %s | Subject: %s | Message preview: %s...",
            recipient,
            title,
            message[:60],
        )
        # Mock SMTP / SES / SendGrid delivery
        msg_id = f"email-{uuid4().hex[:12]}"
        return ProviderDeliveryResult(
            success=True,
            channel="EMAIL",
            recipient=recipient,
            message_id=msg_id,
        )
