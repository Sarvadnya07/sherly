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

## 2026-05-03 - [CRITICAL] Fix Hardcoded API Key and Timing Attack in Remote API
**Vulnerability:** The FastAPI remote server (`remote_api/server.py`) used a hardcoded fallback API key (`"sherly123"`) if `SHERLY_REMOTE_API_KEY` was not set, allowing unauthorized access if deployed without configuration. Furthermore, the key comparison (`x_api_key != API_KEY`) was vulnerable to timing attacks, allowing attackers to incrementally guess the API key.
**Learning:** Hardcoded secrets in core infrastructure code pose an immediate critical risk, particularly when used in authentication middleware. Standard string comparison operators leak timing information proportional to the matched prefix length.
**Prevention:** Fail fast and raise a `RuntimeError` if required security variables (like API keys) are not present in the environment. Always use constant-time comparison functions like `secrets.compare_digest` for security tokens.
