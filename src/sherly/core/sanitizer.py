import re

class LogSanitizer:
    """
    Sanitizes logs for SOC2 compliance.
    Strips API keys, emails, and IP addresses.
    """
    SECRET_PATTERNS = [
        r"sk-[a-zA-Z0-9]{32,}",          # OpenAI
        r"AIza[a-zA-Z0-9_-]{35}",       # Google
        r"sk-ant-[a-z0-9-]{40,}",        # Anthropic
        r"sk-[a-z0-9]{32}",              # Generic / DeepSeek
        r"ghp_[a-zA-Z0-9]{36}",          # GitHub
        r"xox[baprs]-[a-zA-Z0-9-]{10,}", # Slack
    ]
    
    EMAIL_PATTERN = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"
    IP_PATTERN = r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}"

    def sanitize(self, text: str) -> str:
        if not isinstance(text, str):
            return text
            
        # Strip common secrets
        for pattern in self.SECRET_PATTERNS:
            text = re.sub(pattern, "[REDACTED_SECRET]", text)
            
        # Entropy-based detection for high-randomness strings (e.g. generic API keys)
        words = text.split()
        for word in words:
            if len(word) > 24 and self._is_high_entropy(word):
                text = text.replace(word, "[REDACTED_HIGH_ENTROPY]")

        # Strip PII
        text = re.sub(self.EMAIL_PATTERN, "[REDACTED_EMAIL]", text)
        text = re.sub(self.IP_PATTERN, "[REDACTED_IP]", text)
        
        return text

    def _is_high_entropy(self, text: str) -> bool:
        """Simple Shannon entropy check to detect random keys."""
        import math
        if not text: return False
        probs = [text.count(c) / len(text) for c in set(text)]
        entropy = -sum(p * math.log2(p) for p in probs)
        return entropy > 3.5 # Threshold for high-randomness keys
