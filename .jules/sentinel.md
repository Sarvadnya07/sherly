## 2025-02-28 - Removed hardcoded API key from Frontend
**Vulnerability:** The Sherly API key was hardcoded in plaintext in `remote_ui/index.html` as `const API_KEY = "sherly123";`.
**Learning:** Hardcoding secrets in frontend code exposes them directly to anyone with access to the client-side code. This bypasses any authorization mechanisms relying on that secret.
**Prevention:** Do not hardcode API keys or secrets in source files, especially frontend assets. Instead, prompt the user for credentials at runtime or securely provision them from a backend endpoint.
