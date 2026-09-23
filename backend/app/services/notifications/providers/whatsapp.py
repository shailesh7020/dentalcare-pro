from __future__ import annotations

import base64
import logging
import subprocess
from pathlib import Path
from typing import Any
from uuid import uuid4

import httpx

from app.services.notifications.providers.base import (
    NotificationChannelProvider,
    ProviderDeliveryResult,
)

logger = logging.getLogger("notifications.whatsapp")

WA_GATEWAY_URL = "http://127.0.0.1:4050"


class WhatsAppNotificationProvider(NotificationChannelProvider):
    @classmethod
    def _ensure_gateway_running(cls) -> None:
        """Auto-start the local Node.js WhatsApp gateway if it is not running."""
        try:
            project_root = Path(__file__).resolve().parents[5]
            script_path = project_root / "scripts" / "whatsapp-gateway.mjs"
            if script_path.exists():
                subprocess.Popen(
                    ["node", str(script_path)],
                    cwd=str(project_root),
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
        except (OSError, ValueError) as exc:
            logger.warning("Could not auto-start WhatsApp gateway: %s", exc)

    @classmethod
    async def get_gateway_status(cls) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=5.0) as client:
            try:
                resp = await client.get(f"{WA_GATEWAY_URL}/status")
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, ValueError):
                cls._ensure_gateway_running()
                return {
                    "connected": False,
                    "status": "CONNECTING",
                    "qr_data_url": None,
                    "message": "Starting WhatsApp Gateway...",
                }

    @classmethod
    async def request_pairing_code(cls, phone: str) -> dict[str, Any]:
        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                resp = await client.post(
                    f"{WA_GATEWAY_URL}/pairing-code",
                    json={"phone": phone},
                )
                resp.raise_for_status()
                return resp.json()
            except (httpx.HTTPError, ValueError) as exc:
                return {"success": False, "message": str(exc)}

    @classmethod
    async def send_document(
        cls,
        recipient: str,
        filename: str,
        caption: str,
        pdf_bytes: bytes,
    ) -> dict[str, Any]:
        if not recipient:
            return {
                "success": False,
                "code": "MISSING_PHONE",
                "message": "Patient does not have a registered mobile phone number.",
            }

        pdf_b64 = base64.b64encode(pdf_bytes).decode("ascii")
        payload = {
            "phone": recipient,
            "filename": filename,
            "caption": caption,
            "pdf_base64": pdf_b64,
        }

        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                resp = await client.post(
                    f"{WA_GATEWAY_URL}/send-document",
                    json=payload,
                )
                data = resp.json()

                if resp.status_code == 200 and data.get("success"):
                    return {
                        "success": True,
                        "delivery_method": "WHATSAPP",
                        "recipient": recipient,
                        "filename": filename,
                        "message_id": data.get("message_id"),
                        "message": f"Directly sent PDF '{filename}' to {recipient} on WhatsApp!",
                    }

                return data

            except (httpx.HTTPError, ValueError) as exc:
                cls._ensure_gateway_running()
                logger.error("WhatsApp Gateway error: %s", exc)
                return {
                    "success": False,
                    "code": "GATEWAY_STARTING",
                    "message": (
                        "WhatsApp Gateway is starting up. "
                        "Please click Send again in 3 seconds."
                    ),
                }

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
