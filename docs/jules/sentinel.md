## 2024-04-17 - API Endpoint Security
**Vulnerability:** The `/upload` endpoint lacked both authentication and input sanitization, allowing unauthenticated attackers to write files anywhere on the system (Path Traversal).
**Learning:** Security gaps tend to cluster. An endpoint missing basic auth checks is highly likely to also miss input validation.
**Prevention:** Apply the 'verify_key' dependency to all sensitive FastAPI endpoints by default, and use `os.path.basename()` or `Path(file).name` when saving uploaded files.
