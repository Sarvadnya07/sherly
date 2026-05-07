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

## 2026-05-07 - [Hardcoded API Key & Timing Attack]
**Vulnerability:** The API server `remote_api/server.py` had a hardcoded default API key `"sherly123"`, exposing it when the environment variable was missing. Moreover, the key comparison used standard inequality `!=`, which makes it vulnerable to a timing attack.
**Learning:** Hardcoded default credentials allow attackers to trivially bypass authentication if misconfigured. Simple equality checks allow timing attacks since the comparison stops as soon as a character mismatch occurs.
**Prevention:** Remove fallback secrets and enforce explicit configuration by crashing the server if missing. Use constant-time comparisons like `secrets.compare_digest` for validating authentication tokens.
