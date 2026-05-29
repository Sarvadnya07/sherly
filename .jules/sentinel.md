## 2024-05-18 - Hardcoded API Key and Timing Attack Vulnerability in FastAPI Auth
**Vulnerability:** The FastAPI application used a hardcoded default API key (`"sherly123"`) if the environment variable was missing. Additionally, the string comparison for the API key was vulnerable to timing attacks.
**Learning:** Hardcoded fallback values for secrets undermine security configuration. Direct string comparison for secrets leaks information through execution time.
**Prevention:** Remove default fallbacks for secrets, fail securely if not configured. Always use `secrets.compare_digest` for secret comparison.

## 2024-05-24 - API Security Refactoring
**Vulnerability:** Path traversal via unsanitized file upload name (`file.filename`), missing authentication on the `/upload` endpoint, and information disclosure through stack traces in the `/command` endpoint. Also exposed API keys via URL query params (`key`).
**Learning:** These vulnerabilities expose internal systems and file structures. Path traversal allows writing files to arbitrary locations. Unauthenticated uploads allow unauthorized data ingestion. Query params are often logged, leaking secrets. Unhandled exceptions disclose internal architecture.
**Prevention:** Always use `Path(file.filename).name` or equivalent to sanitize filenames. Apply authorization checks uniformly (e.g., `Depends(verify_key)`) across all sensitive endpoints. Pass secrets exclusively via headers. Catch exceptions globally and log them securely using dedicated loggers, returning generic error messages to the client.

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
## 2023-10-28 - Incomplete Security Patching Leads to Runtime Errors
**Vulnerability:** A security patch replaced a vulnerable `run_command` with a safe alternative `safe_exec`, but failed to ensure the newly imported `safe_exec` was implemented or available in the module imported from, which would cause an `ImportError` in runtime.
**Learning:** Renaming an import or method call without verifying its availability in the dependency tree will break code execution. Testing is critical to ensure both security logic is correctly applied and the application continues to run without missing dependency exceptions.
**Prevention:** Verify all imported modules exist and are available in the scope they are used. Run the appropriate tests to ensure application runs flawlessly after refactoring.
