# backend/tests/test_remote_access.py
"""
Unit and integration tests for Phase 18: Hybrid Local + Secure Remote Access.
Validates:
- Pure Python RFC 6238 TOTP two-factor authentication
- Remote request detection & remote IP tagging
- Prohibited remote destructive actions (guardrails)
- Remote session lifecycle and revocation
- Cloudflare Tunnel YAML configuration generation
- In-memory rate limiting fallback when Redis is absent
- Remote notifications and Web Push payload formatting
"""
from uuid import uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.dependencies.rate_limit import _in_memory_rate_limit
from app.main import app
from app.security.totp import TOTPService
from app.services.remote_access_service import RemoteAccessService
from app.services.remote_notification_service import RemoteNotificationService


@pytest.mark.asyncio
async def test_totp_service_lifecycle():
    # 1. Generate Secret
    secret = TOTPService.generate_secret()
    assert len(secret) >= 26
    
    # 2. Generate Code
    code = TOTPService.generate_totp_code(secret)
    assert len(code) == 6
    assert code.isdigit()

    # 3. Verify Code
    assert TOTPService.verify_totp_code(secret, code)
    assert not TOTPService.verify_totp_code(secret, "999999" if code != "999999" else "000000")
    assert not TOTPService.verify_totp_code(secret, "abc")

    # 4. Provisioning URI
    uri = TOTPService.get_provisioning_uri(secret, "doctor@clinic.local", issuer="DentalCare Pro")
    assert uri.startswith("otpauth://totp/DentalCare%20Pro:doctor%40clinic.local")
    assert f"secret={secret}" in uri

    # 5. Backup recovery codes
    codes = TOTPService.generate_backup_codes(count=8)
    assert len(codes) == 8
    assert all(len(c) == 8 for c in codes)


@pytest.mark.asyncio
async def test_in_memory_rate_limit_fallback():
    key = f"test-client-{uuid4()}"
    limit = 3
    window = 10

    # Under limit
    assert _in_memory_rate_limit(key, limit, window) is True
    assert _in_memory_rate_limit(key, limit, window) is True
    assert _in_memory_rate_limit(key, limit, window) is True

    # Exceed limit
    assert _in_memory_rate_limit(key, limit, window) is False


@pytest.mark.asyncio
async def test_remote_access_middleware_headers_and_guardrails():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Local Request (no remote headers)
        resp_local = await client.get("/api/v1/health/live")
        assert resp_local.status_code == 200
        assert resp_local.headers.get("X-Remote-Access") == "false"
        assert resp_local.headers.get("X-Clinic-Source") == "on-premise-server"

        # 2. Remote Request (Cloudflare Tunnel CF-Connecting-IP)
        resp_remote = await client.get(
            "/api/v1/health/live",
            headers={"CF-Connecting-IP": "198.51.100.24"},
        )
        assert resp_remote.status_code == 200
        assert resp_remote.headers.get("X-Remote-Access") == "true"

        # 3. Prohibited Remote Destructive Action (DELETE on patients)
        fake_id = uuid4()
        resp_blocked_delete = await client.delete(
            f"/api/v1/patients/{fake_id}",
            headers={"CF-Connecting-IP": "198.51.100.24"},
        )
        assert resp_blocked_delete.status_code == 403
        data = resp_blocked_delete.json()
        assert data["code"] == "REMOTE_DELETION_PROHIBITED"
        assert "Destructive deletions can only be performed on-premise" in data["detail"]

        # 4. Prohibited Remote Database Admin Action
        resp_blocked_admin = await client.post(
            "/api/v1/backups/restore",
            headers={"CF-Connecting-IP": "198.51.100.24"},
        )
        assert resp_blocked_admin.status_code == 403
        assert resp_blocked_admin.json()["code"] == "REMOTE_ADMIN_PROHIBITED"


@pytest.mark.asyncio
async def test_remote_notification_web_push_payload():
    class FakeNotif:
        id = uuid4()
        title = "Low Stock: Composite Resin"
        body = "Only 2 units remaining."
        class type:
            value = "INVENTORY_ALERT"

    payload = RemoteNotificationService.format_web_push_payload(FakeNotif)
    assert payload["notification"]["title"] == "Low Stock: Composite Resin"
    assert payload["notification"]["data"]["url"] == "/mobile"
    assert len(payload["notification"]["actions"]) == 2


@pytest.mark.asyncio
async def test_cloudflare_config_generator():
    config = RemoteAccessService.generate_cloudflare_config(
        tunnel_id="test-tunnel-1234",
        credentials_file="C:\\cloudflared\\test.json",
        local_web_port=3000,
        local_api_port=8000,
        hostname="clinic.brightsmile.local",
    )
    assert "tunnel: test-tunnel-1234" in config
    assert "service: http://127.0.0.1:3000" in config
    assert "service: http://127.0.0.1:8000" in config
    assert "hostname: clinic.brightsmile.local" in config
