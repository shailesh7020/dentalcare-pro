# backend/app/security/totp.py
"""
DentalCare Pro - Pure Python RFC 6238 Two-Factor Authentication (TOTP)
Standard-library implementation with zero external dependencies.
Compatible with Google Authenticator, Microsoft Authenticator, 1Password, etc.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import secrets
import struct
import time
import urllib.parse


class TOTPService:
    @staticmethod
    def generate_secret(byte_length: int = 20) -> str:
        """Generate a random base32 encoded secret key (RFC 4648)."""
        raw_bytes = secrets.token_bytes(byte_length)
        return base64.b32encode(raw_bytes).decode("utf-8").replace("=", "")

    @staticmethod
    def generate_backup_codes(count: int = 8) -> list[str]:
        """Generate one-time emergency recovery codes."""
        return [secrets.token_hex(4).upper() for _ in range(count)]

    @classmethod
    def generate_totp_code(
        cls,
        secret: str,
        timestamp: float | None = None,
        interval: int = 30,
        digits: int = 6,
    ) -> str:
        """Calculate the 6-digit TOTP code for a secret and timestamp."""
        if timestamp is None:
            timestamp = time.time()

        counter = int(timestamp // interval)
        return cls._hotp(secret, counter, digits=digits)

    @classmethod
    def verify_totp_code(
        cls,
        secret: str,
        code: str,
        window: int = 1,
        interval: int = 30,
        digits: int = 6,
    ) -> bool:
        """Verify a user-submitted TOTP code allowing +/- window intervals clock drift."""
        clean_code = str(code).strip().replace(" ", "")
        if len(clean_code) != digits or not clean_code.isdigit():
            return False

        now = time.time()
        current_counter = int(now // interval)

        for drift in range(-window, window + 1):
            expected = cls._hotp(secret, current_counter + drift, digits=digits)
            if hmac.compare_digest(expected, clean_code):
                return True
        return False

    @staticmethod
    def get_provisioning_uri(
        secret: str,
        account_name: str,
        issuer: str = "DentalCare Pro",
    ) -> str:
        """Generate otpauth:// URI for scanning with mobile authenticator apps."""
        escaped_issuer = urllib.parse.quote(issuer)
        escaped_account = urllib.parse.quote(account_name)
        label = f"{escaped_issuer}:{escaped_account}"
        return (
            f"otpauth://totp/{label}"
            f"?secret={secret}"
            f"&issuer={escaped_issuer}"
            f"&algorithm=SHA1"
            f"&digits=6"
            f"&period=30"
        )

    @classmethod
    def _hotp(cls, secret: str, counter: int, digits: int = 6) -> str:
        """HMAC-based One-Time Password algorithm (RFC 4226)."""
        # Normalize secret and add base32 padding if needed
        clean_secret = secret.strip().upper()
        padding_needed = (8 - len(clean_secret) % 8) % 8
        padded_secret = clean_secret + ("=" * padding_needed)

        key_bytes = base64.b32decode(padded_secret, casefold=True)
        counter_bytes = struct.pack(">Q", counter)

        mac = hmac.new(key_bytes, counter_bytes, hashlib.sha1).digest()
        offset = mac[19] & 0x0F
        binary = struct.unpack(">I", mac[offset : offset + 4])[0] & 0x7FFFFFFF
        otp = binary % (10**digits)
        return f"{otp:0{digits}d}"
