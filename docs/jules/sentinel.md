## 2025-05-24 - Missing Auth and Path Traversal on Upload Endpoint
**Vulnerability:** The `/upload` endpoint in FastAPI was unauthenticated and the uploaded `file.filename` was appended directly to `UPLOAD_DIR`, creating a path traversal vulnerability.
**Learning:** Incomplete or inconsistent authentication rules across FastAPI routes can easily lead to exposed endpoints, and trusting raw file names directly from the client request can lead to saving files outside the designated directory.
**Prevention:** Apply dependency injection like `Depends(verify_key)` to all sensitive endpoints, not just some, and always sanitize `filename` variables from requests by using `Path(filename).name` or `os.path.basename` before appending to paths.
