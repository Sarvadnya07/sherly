## 2024-05-24 - API Security Fixes (Path Traversal, Auth Bypass, Error Leakage)
**Vulnerability:**
1. The `/upload` endpoint lacked authentication entirely, allowing unauthenticated file uploads.
2. The `/upload` endpoint directly appended `file.filename` to `UPLOAD_DIR` without sanitization, creating a Path Traversal vulnerability where an attacker could upload files to arbitrary locations.
3. The `/command` endpoint leaked sensitive application state and stack traces by returning `str(exc)` upon exception.
4. The `/command` endpoint had redundant and unsafe query parameter authentication logic that could potentially bypass or complicate the standard Header-based auth dependency `verify_key`.

**Learning:**
1. Missing authentication on endpoints is a critical risk, especially for actions like file uploads.
2. User-provided filenames must never be trusted or used directly in file paths, as they can contain `../` or absolute paths.
3. Returning raw exception messages directly to the client is a significant security risk, as it leaks internal application details that attackers can use to craft more targeted attacks.
4. Relying on custom inline authentication logic rather than centralized, tested dependency injection (`Depends`) introduces complexity and potential vulnerabilities.

**Prevention:**
1. Always apply standard authentication dependencies (e.g., `Depends(verify_key)`) to all sensitive endpoints, including file uploads.
2. Always sanitize user-provided filenames using `Path(filename).name` or `os.path.basename` before using them in file operations.
3. Catch generic exceptions and return generic, uninformative error messages (e.g., "Internal server error") to the client.
4. Use standard, framework-provided dependency injection for authentication and avoid custom query parameter-based overrides.