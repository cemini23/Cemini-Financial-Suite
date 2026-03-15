"""Cemini Financial Suite — Robinhood MFA Handler (Step 49f).

Generates TOTP codes for Robinhood's two-factor authentication using
the pyotp library.  Falls back gracefully if pyotp is not installed.

Env vars:
  ROBINHOOD_MFA_SECRET   Base-32 TOTP secret from Robinhood 2FA setup
                         (the secret shown when scanning the QR code)

Usage:
    handler = MFAHandler()
    code = handler.get_current_code()   # → "123456" or None
"""
from __future__ import annotations

import logging
import os
from typing import Optional

logger = logging.getLogger("shared.safety.mfa_handler")

_SECRET_ENV = "ROBINHOOD_MFA_SECRET"


class MFAHandler:
    """TOTP-based MFA code generator for Robinhood.

    Args:
        secret: Base-32 TOTP secret.  If None, reads ROBINHOOD_MFA_SECRET env var.
    """

    def __init__(self, secret: Optional[str] = None) -> None:
        self._secret = secret or os.getenv(_SECRET_ENV, "")
        self._pyotp = self._load_pyotp()

    # ── Public interface ────────────────────────────────────────────────────

    def is_configured(self) -> bool:
        """Return True if a TOTP secret is available."""
        return bool(self._secret and self._pyotp is not None)

    def get_current_code(self) -> Optional[str]:
        """Return the current 6-digit TOTP code, or None if unavailable."""
        if not self.is_configured():
            logger.warning(
                "MFAHandler: TOTP not configured — set %s env var.", _SECRET_ENV
            )
            return None
        try:
            totp = self._pyotp.TOTP(self._secret)  # type: ignore[union-attr]
            code = totp.now()
            logger.debug("MFAHandler: TOTP code generated.")
            return code
        except Exception as exc:  # noqa: BLE001
            logger.error("MFAHandler: TOTP generation failed: %s", exc)
            return None

    def verify_code(self, code: str) -> bool:
        """Verify a TOTP code (valid window ±1 step = ±30 s)."""
        if not self.is_configured():
            return False
        try:
            totp = self._pyotp.TOTP(self._secret)  # type: ignore[union-attr]
            return totp.verify(code, valid_window=1)
        except Exception as exc:  # noqa: BLE001
            logger.error("MFAHandler: TOTP verify failed: %s", exc)
            return False

    def provisioning_uri(self, account_name: str = "Cemini", issuer: str = "Robinhood") -> Optional[str]:
        """Return an otpauth:// URI for QR code generation (useful for re-enrollment)."""
        if not self.is_configured():
            return None
        try:
            totp = self._pyotp.TOTP(self._secret)  # type: ignore[union-attr]
            return totp.provisioning_uri(name=account_name, issuer_name=issuer)
        except Exception as exc:  # noqa: BLE001
            logger.error("MFAHandler: provisioning_uri failed: %s", exc)
            return None

    # ── Private helpers ─────────────────────────────────────────────────────

    @staticmethod
    def _load_pyotp():
        """Import pyotp, returning None if not installed."""
        try:
            import pyotp  # type: ignore[import]
            return pyotp
        except ImportError:
            logger.warning(
                "MFAHandler: pyotp not installed — MFA disabled. "
                "Install with: pip install pyotp"
            )
            return None
