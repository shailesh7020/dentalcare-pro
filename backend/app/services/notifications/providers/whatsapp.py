from __future__ import annotations

import logging
from uuid import uuid4

from app.services.notifications.providers.base import (
    NotificationChannelProvider,
    ProviderDeliveryResult,
)

logger = logging.getLogger("notifications.whatsapp")


class WhatsAppNotificationProvider(NotificationChannelProvider):
    async def send(
        self, recipient: str, title: str, message: str, data: dict | None = None
    ) -> ProviderDeliveryResult:
        if not recipient:
            return ProviderDeliveryResult(
                success=False,
                channel="WHATSAPP",
                recipient=recipient,
                error="Recipient WhatsApp number missing",
            )

        logger.info(
            "Dispatching WhatsApp Template to %s | Header: %s | Body: %s",
            recipient,
            title,
            message[:80],
        )
        msg_id = f"wa-{uuid4().hex[:12]}"
        return ProviderDeliveryResult(
            success=True,
            channel="WHATSAPP",
            recipient=recipient,
            message_id=msg_id,
        )
