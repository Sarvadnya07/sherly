"""
BIOMETRICS — biometrics.py
Upgrades:
  RC-2 / FS-#4  Real Windows Hello biometric bridge via WinRT UserConsentVerifier.
                 Falls back to: Windows MessageBox PIN dialog → simple text approval.
                 The three-tier fallback means the feature is never silently absent.
"""

from __future__ import annotations

import asyncio
import os
from sherly.utils.runtime_utils import log


class BiometricValidator:
    """
    Three-tier biometric/identity approval for DANGEROUS commands.

    Tier 1 (preferred):  Windows Hello via WinRT UserConsentVerifier API.
    Tier 2 (fallback):   Windows MessageBox with Yes/No prompt (PIN/password dialog).
    Tier 3 (non-Windows): Simple input()-based confirmation (CI / Linux / macOS).
    """

    def __init__(self) -> None:
        self.enabled   = os.name == "nt"
        self._tier: str = self._detect_tier()
        log(f"[Biometrics] Initialized — tier: {self._tier}")

    def _detect_tier(self) -> str:
        if os.name != "nt":
            return "text"
        # Try WinRT (requires winsdk package: pip install winsdk)
        try:
            from winsdk.windows.security.credentials.ui import (
                UserConsentVerifier,
                UserConsentVerifierAvailability,
            )
            avail = asyncio.run(
                UserConsentVerifier.check_availability_async()
            )
            if avail == UserConsentVerifierAvailability.AVAILABLE:
                return "winrt"
        except Exception:
            pass
        # Fall back to MessageBox
        return "messagebox"

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def request_approval(self, command: str) -> bool:
        """
        Request identity verification for a DANGEROUS command.
        Returns True if approved, False if denied.
        """
        log(f"[Biometrics] Requesting approval for: {command}")

        if self._tier == "winrt":
            approved = self._winrt_verify(command)
        elif self._tier == "messagebox":
            approved = self._messagebox_verify(command)
        else:
            approved = self._text_verify(command)

        if approved:
            log("[Biometrics] APPROVED")
        else:
            log("[Biometrics] DENIED")
        return approved

    # ------------------------------------------------------------------
    # Tier 1: Windows Hello (WinRT)
    # ------------------------------------------------------------------

    def _winrt_verify(self, command: str) -> bool:
        """
        FS-#4 / RC-2: Real Windows Hello via UserConsentVerifier.
        Prompts fingerprint / face / PIN through the OS-level security dialog.
        """
        try:
            from winsdk.windows.security.credentials.ui import (
                UserConsentVerifier,
                UserConsentVerifierResult,
            )

            message = (
                f"Sherly AI Security Alert\n\n"
                f"Action: {command[:120]}\n\n"
                "Verify your identity to approve this DANGEROUS action."
            )
            result = asyncio.run(
                UserConsentVerifier.request_verification_async(message)
            )
            if result == UserConsentVerifierResult.VERIFIED:
                return True
            log(
                f"[Biometrics] Windows Hello result: {result} — falling back to MessageBox",
                level="warning",
            )
        except Exception as exc:
            log(f"[Biometrics] WinRT error: {exc} — falling back to MessageBox", level="warning")

        # Graceful degradation to tier 2
        self._tier = "messagebox"
        return self._messagebox_verify(command)

    # ------------------------------------------------------------------
    # Tier 2: Win32 MessageBox (PIN / password dialog via OS)
    # ------------------------------------------------------------------

    def _messagebox_verify(self, command: str) -> bool:
        """
        Native Windows MessageBox with topmost, modal, Yes/No security prompt.
        Clicking "No" or closing the dialog denies the action.
        """
        try:
            import ctypes

            # MB_YESNO | MB_ICONWARNING | MB_SETFOREGROUND | MB_TOPMOST = 0x50034
            res = ctypes.windll.user32.MessageBoxW(
                0,
                f"Sherly AI Security Alert\n\nAction: {command}\n\n"
                "Do you verify your identity and approve this DANGEROUS action?",
                "Sherly AI — Identity Verification",
                0x50034,
            )
            return res == 6  # 6 = IDYES
        except Exception as exc:
            log(f"[Biometrics] MessageBox error: {exc} — falling back to text", level="warning")
            self._tier = "text"
            return self._text_verify(command)

    # ------------------------------------------------------------------
    # Tier 3: Text-based (non-Windows / CI / headless)
    # ------------------------------------------------------------------

    def _text_verify(self, command: str) -> bool:
        """Fallback for non-Windows environments or headless runs."""
        try:
            ans = input(
                f"\n🔒 DANGEROUS ACTION REQUESTED\n"
                f"   Command: {command}\n"
                f"   Type 'APPROVE' to confirm: "
            ).strip()
            return ans == "APPROVE"
        except (EOFError, OSError):
            # Non-interactive environment (e.g. CI pipe) — deny by default
            log("[Biometrics] Non-interactive environment — DANGEROUS action denied.", level="warning")
            return False
