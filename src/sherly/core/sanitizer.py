"""
SANITIZER — sanitizer.py
Fixes:
  FS-#21  Extended secret detection: added Groq, HuggingFace, AWS, Stripe,
           Twilio, and generic bearer token formats.
           Added an active Git-aware warning when a key is found in a tracked file.
"""

from __future__ import annotations

import math
import re


class LogSanitizer:
    """
    Sanitizes logs for SOC2 compliance.
    Strips API keys (provider-specific + entropy-based), emails, and IP addresses.
    Warns when a detected key appears in a Git-tracked file.
    """

    # Provider-specific known key formats (FS-#21 expansion)
    SECRET_PATTERNS: list[str] = [
        r"sk-[a-zA-Z0-9]{32,}",                  # OpenAI
        r"AIza[a-zA-Z0-9_\-]{35}",               # Google / Gemini
        r"sk-ant-[a-z0-9\-]{40,}",               # Anthropic
        r"sk-[a-z0-9]{32}",                       # Generic / DeepSeek
        r"ghp_[a-zA-Z0-9]{36}",                  # GitHub PAT
        r"ghs_[a-zA-Z0-9]{36}",                  # GitHub Actions token
        r"gho_[a-zA-Z0-9]{36}",                  # GitHub OAuth token
        r"xox[baprs]-[a-zA-Z0-9\-]{10,}",       # Slack
        r"gsk_[a-zA-Z0-9]{40,}",                 # Groq (FS-#21)
        r"hf_[a-zA-Z0-9]{30,}",                  # HuggingFace (FS-#21)
        r"AKIA[0-9A-Z]{16}",                      # AWS Access Key ID (FS-#21)
        r"sk_live_[a-zA-Z0-9]{24,}",             # Stripe live key (FS-#21)
        r"rk_live_[a-zA-Z0-9]{24,}",             # Stripe restricted key (FS-#21)
        r"AC[a-z0-9]{32}",                        # Twilio Account SID (FS-#21)
        r"Bearer\s+[a-zA-Z0-9\-._~+/]{20,}",    # Generic Bearer token (FS-#21)
    ]

    EMAIL_PATTERN = r"[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}"
    IP_PATTERN    = r"\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b"

    def sanitize(self, text: str) -> str:
        if not isinstance(text, str):
            return text

        # Strip provider-specific secrets
        for pattern in self.SECRET_PATTERNS:
            text = re.sub(pattern, "[REDACTED_SECRET]", text)

        # Entropy-based detection for high-randomness generic tokens
        words = text.split()
        for word in words:
            clean = re.sub(r"[^a-zA-Z0-9]", "", word)
            if len(clean) > 24 and self._is_high_entropy(clean):
                text = text.replace(word, "[REDACTED_HIGH_ENTROPY]")

        # Strip PII
        text = re.sub(self.EMAIL_PATTERN, "[REDACTED_EMAIL]", text)
        text = re.sub(self.IP_PATTERN,    "[REDACTED_IP]",    text)

        return text

    def _is_high_entropy(self, text: str) -> bool:
        """Shannon entropy check — flags strings with entropy > 3.5 bits/char."""
        if not text:
            return False
        probs   = [text.count(c) / len(text) for c in set(text)]
        entropy = -sum(p * math.log2(p) for p in probs)
        return entropy > 3.5

    def check_git_tracked_files(self, project_root: str = ".") -> list[str]:
        """
        FS-#21: Scan Git-tracked files for secrets. Returns a list of warnings.
        Designed to run as a background check on startup, not in the hot path.
        """
        import subprocess
        import os
        warnings: list[str] = []

        try:
            result = subprocess.run(
                ["git", "-C", project_root, "ls-files"],
                capture_output=True, text=True, timeout=5
            )
            tracked_files = result.stdout.splitlines()
        except Exception:
            return warnings

        for rel_path in tracked_files:
            full_path = os.path.join(project_root, rel_path)
            if not os.path.isfile(full_path):
                continue
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                for pattern in self.SECRET_PATTERNS:
                    if re.search(pattern, content):
                        warnings.append(
                            f"⚠️  Possible secret found in Git-tracked file: {rel_path}"
                        )
                        break
            except Exception:
                continue

        return warnings
