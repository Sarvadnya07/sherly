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

## 2023-10-27 - [Command Injection via Unvalidated System Commands]
**Vulnerability:** The System Agent (`system_agent.py`) executed arbitrary OS commands via the raw `run_command` function without validation.
**Learning:** System automation agents that execute parsed LLM output or user input as shell commands must always use a central validation gateway (whitelist/safety guard). Direct calls to raw execution functions bypass security layers.
**Prevention:** Always use `safe_exec` from `sherly.tools.terminal_tools` instead of `run_command` when dynamically executing shell commands from external inputs or LLM generation.

## 2026-04-27 - Hardcoded API Key & Timing Attack in API Authentication
**Vulnerability:** The API server (`src/sherly/remote_api/server.py`) had a hardcoded default API key (`"sherly123"`) as a fallback if the environment variable was missing. In addition, the authentication check `verify_key` compared the incoming key and expected key using the `!=` operator, making it vulnerable to a timing attack.
**Learning:** Hardcoded default secrets can be easily exploited if a production environment misses an environment variable configuration. Furthermore, standard string comparison operators in Python evaluate character-by-character and return early upon mismatch. This allows an attacker to brute force the API key by analyzing response times.
**Prevention:**
- Do not provide a fallback for sensitive environment variables; fail securely when required secrets are not provided.
- Always use constant-time comparison methods like `secrets.compare_digest` from the built-in `secrets` module when verifying security credentials, tokens, or API keys.
