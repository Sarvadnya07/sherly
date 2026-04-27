## 2024-05-24 - Unauthenticated Path Traversal in Uploads
**Vulnerability:** The `/upload` endpoint lacked authentication and used raw `file.filename` directly in a file path, allowing an unauthenticated attacker to upload files to arbitrary locations (path traversal).
**Learning:** Even internal or utility endpoints need explicit authentication dependencies (like `Depends(verify_key)`) and user-provided filenames must never be trusted; they must be sanitized.
**Prevention:** Always use `Path(filename).name` to extract just the file name securely, and enforce authentication globally or explicitly on all sensitive endpoints.
## 2025-05-24 - Missing Auth and Path Traversal on Upload Endpoint
**Vulnerability:** The `/upload` endpoint in FastAPI was unauthenticated and the uploaded `file.filename` was appended directly to `UPLOAD_DIR`, creating a path traversal vulnerability.
**Learning:** Incomplete or inconsistent authentication rules across FastAPI routes can easily lead to exposed endpoints, and trusting raw file names directly from the client request can lead to saving files outside the designated directory.
**Prevention:** Apply dependency injection like `Depends(verify_key)` to all sensitive endpoints, not just some, and always sanitize `filename` variables from requests by using `Path(filename).name` or `os.path.basename` before appending to paths.
## 2024-04-17 - API Endpoint Security
**Vulnerability:** The `/upload` endpoint lacked both authentication and input sanitization, allowing unauthenticated attackers to write files anywhere on the system (Path Traversal).
**Learning:** Security gaps tend to cluster. An endpoint missing basic auth checks is highly likely to also miss input validation.
**Prevention:** Apply the 'verify_key' dependency to all sensitive FastAPI endpoints by default, and use `os.path.basename()` or `Path(file).name` when saving uploaded files.

## 2024-04-22 - Path Traversal and Auth Bypass in API
**Vulnerability:** The `/upload` endpoint lacked authentication and used unsanitized filenames directly in the file path (`UPLOAD_DIR / file.filename`), allowing path traversal. Additionally, `/command` permitted API keys in query parameters and leaked raw exception traces.
**Learning:** Even internal or utility API endpoints must use uniform authentication dependencies (`Depends(verify_key)`) and validate external input strictly (using `Path().name`) to prevent bypassing controls or writing files outside the designated directory. Exposing exceptions to clients also leaks server structure.
**Prevention:** Always apply the standard authentication dependency to all sensitive endpoints, sanitize file uploads by extracting just the name `Path(filename).name`, and ensure all endpoints log exceptions internally while returning generic error messages to the client.
