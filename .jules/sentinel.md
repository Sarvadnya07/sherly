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

## 2023-10-27 - Hardcoded Secrets in Frontend Assets
**Vulnerability:** The API Key was hardcoded as a fallback in the `remote_api/server.py` and strictly in the frontend script `remote_ui/index.html`. This exposes the API Key to any user of the web application.
**Learning:** Hardcoded credentials on the frontend or as a default in the backend are a critical security vulnerability, as static HTML and JS are delivered entirely to the client's browser, giving full access to sensitive API endpoints.
**Prevention:** Never hardcode secrets in frontend code. Utilize dynamic retrieval logic, such as prompting the user for an API key and securely persisting it locally with `localStorage`. In the backend, fail fast and securely without an API key rather than falling back to a hardcoded string.
