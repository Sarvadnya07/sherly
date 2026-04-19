## 2024-05-24 - Unauthenticated Path Traversal in Uploads
**Vulnerability:** The `/upload` endpoint lacked authentication and used raw `file.filename` directly in a file path, allowing an unauthenticated attacker to upload files to arbitrary locations (path traversal).
**Learning:** Even internal or utility endpoints need explicit authentication dependencies (like `Depends(verify_key)`) and user-provided filenames must never be trusted; they must be sanitized.
**Prevention:** Always use `Path(filename).name` to extract just the file name securely, and enforce authentication globally or explicitly on all sensitive endpoints.
