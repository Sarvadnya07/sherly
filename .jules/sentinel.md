## 2024-05-24 - [CRITICAL] Fix hardcoded API key and timing attack vulnerability
**Vulnerability:** The API key verification for the remote server had two vulnerabilities:
1. `API_KEY` defaulted to a hardcoded string (`"sherly123"`) if the `SHERLY_REMOTE_API_KEY` environment variable was not set.
2. The `verify_key` function used standard equality comparison (`x_api_key != API_KEY`), which is susceptible to timing attacks.

**Learning:**
1. Hardcoded secrets are a critical security risk as they can be easily discovered in version control or by unauthorized users.
2. Standard equality checks exit early on mismatch, allowing attackers to guess the key character by character by measuring the response time (timing attack).

**Prevention:**
1. Never use hardcoded secrets or fallback values for authentication tokens. Require them to be set securely via environment variables or secret management systems. Ensure the application fails to start or rejects requests if the key is missing.
2. Always use `secrets.compare_digest` (or equivalent constant-time comparison functions) for comparing sensitive strings like passwords, API keys, or tokens.