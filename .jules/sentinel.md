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

## 2026-05-06 - Missing Timing Attack Protection in API Authentication
**Vulnerability:** The API server (`remote_api/server.py`) checked the API key using a standard string comparison (`x_api_key != API_KEY`), which is vulnerable to timing attacks. It also had a hardcoded default fallback for the `SHERLY_REMOTE_API_KEY`.
**Learning:** Using `!=` for token or key comparisons evaluates characters sequentially, allowing attackers to infer correct characters based on response times. Hardcoded defaults for API keys allow trivial circumvention if the environment is not configured.
**Prevention:**
- Always use `secrets.compare_digest()` for comparing security tokens, keys, or passwords.
- Fail securely when expected security environment variables are missing (e.g. by raising a `RuntimeError`) rather than falling back to default strings.
