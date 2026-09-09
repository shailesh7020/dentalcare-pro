from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request
from starlette.responses import Response

from app.middleware.remote_access import (
    RemoteAccessMiddleware,
    is_private_ip,
)
from app.security.totp import TOTPService


def test_private_ip_detection():
    """Verify classification of LAN vs Public IPs."""
    assert is_private_ip("127.0.0.1") is True
    assert is_private_ip("192.168.1.50") is True
    assert is_private_ip("10.0.0.15") is True
    assert is_private_ip("172.20.5.1") is True
    assert is_private_ip("::1") is True

    # Public internet IPs
    assert is_private_ip("8.8.8.8") is False
    assert is_private_ip("104.21.50.12") is False
    assert is_private_ip("203.0.113.195") is False
    assert is_private_ip("invalid-ip") is False


def test_totp_service_lifecycle():
    """Verify RFC 6238 TOTP key generation, provisioning URI, and time drift verification."""
    secret = TOTPService.generate_secret()
    assert len(secret) == 32

    uri = TOTPService.get_provisioning_uri(
        secret=secret,
        account_name="doctor@dentalcare.com",
        issuer="DentalCare Pro",
    )
    assert "otpauth://totp/" in uri
    assert "doctor" in uri
    assert "DentalCare" in uri
    assert "secret=" in uri

    # Current token
    token = TOTPService.generate_totp_code(secret)
    assert len(token) == 6
    assert token.isdigit()

    # Immediate verification
    assert TOTPService.verify_totp_code(secret, token, window=1) is True

    # Bad token
    assert TOTPService.verify_totp_code(secret, "000000", window=1) is False


@pytest.mark.asyncio
async def test_remote_access_middleware_blocks_remote_delete():
    """Verify remote requests attempting to delete records receive 403 Forbidden."""
    middleware = RemoteAccessMiddleware(app=MagicMock())

    # Simulate remote request via CF-Connecting-IP
    scope = {
        "type": "http",
        "method": "DELETE",
        "path": "/api/v1/patients/123e4567-e89b-12d3-a456-426614174000",
        "headers": [
            (b"cf-connecting-ip", b"203.0.113.50"),
            (b"host", b"clinic.example.com"),
        ],
        "client": ("127.0.0.1", 54321),
    }
    request = Request(scope)
    call_next = AsyncMock()

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 403
    call_next.assert_not_called()


@pytest.mark.asyncio
async def test_remote_access_middleware_allows_local_delete():
    """Verify on-premise LAN requests are permitted to execute delete operations."""
    middleware = RemoteAccessMiddleware(app=MagicMock())

    scope = {
        "type": "http",
        "method": "DELETE",
        "path": "/api/v1/patients/123e4567-e89b-12d3-a456-426614174000",
        "headers": [(b"host", b"192.168.1.10:8000")],
        "client": ("192.168.1.25", 54321),  # Local LAN PC
    }
    request = Request(scope)
    expected_response = Response(status_code=200)
    call_next = AsyncMock(return_value=expected_response)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_called_once()


@pytest.mark.asyncio
async def test_remote_access_middleware_allows_remote_safe_operations():
    """Verify remote requests for schedule review and clinical lookups are permitted."""
    middleware = RemoteAccessMiddleware(app=MagicMock())

    scope = {
        "type": "http",
        "method": "GET",
        "path": "/api/v1/mobile/dashboard",
        "headers": [
            (b"cf-connecting-ip", b"203.0.113.50"),
            (b"host", b"clinic.example.com"),
        ],
        "client": ("127.0.0.1", 54321),
    }
    request = Request(scope)
    expected_response = Response(status_code=200)
    call_next = AsyncMock(return_value=expected_response)

    response = await middleware.dispatch(request, call_next)

    assert response.status_code == 200
    call_next.assert_called_once()
