## 2024-05-18 - Hardcoded API Key and Timing Attack Vulnerability in FastAPI Auth
**Vulnerability:** The FastAPI application used a hardcoded default API key ("sherly123") if the environment variable was missing. Additionally, the string comparison for the API key was vulnerable to timing attacks.
**Learning:** Hardcoded fallback values for secrets undermine security configuration. Direct string comparison for secrets leaks information through execution time.
**Prevention:** Remove default fallbacks for secrets, fail securely if not configured. Always use `secrets.compare_digest` for secret comparison.
