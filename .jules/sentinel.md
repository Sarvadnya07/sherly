## 2024-05-13 - [CRITICAL] Fix hardcoded API key fallback and timing attack in remote API

**Vulnerability:**
The `remote_api/server.py` had a hardcoded default API key `"sherly123"` using `os.getenv("SHERLY_REMOTE_API_KEY", "sherly123")`. Additionally, it compared the incoming API key using a standard `!=` string comparison instead of a constant-time comparison, opening it up to timing attacks.

**Learning:**
Relying on hardcoded fallbacks for critical secrets nullifies environment-based configuration security. Simple string equality operators on secrets leak comparison time, potentially allowing an attacker to deduce the correct key byte-by-byte. This pattern is common in quick development iterations but must be replaced for production.

**Prevention:**
Always read secrets from the environment *without* a fallback, and immediately raise a loud exception (e.g., `RuntimeError`) on startup if the secret is missing to "fail securely". Always use `secrets.compare_digest(a, b)` for comparing secure tokens or passwords to prevent timing attacks.
