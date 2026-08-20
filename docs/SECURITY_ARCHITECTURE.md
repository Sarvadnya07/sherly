# Sherly Application & API Security Architecture (Phase 13)

**Target Scope**: System-wide Security Boundaries, Authentication, Authorization, and IPC  
**Classification**: Zero-Trust Security Specification  
**Status**: ACTIVE & PRODUCTION-CERTIFIED  

---

## 1. Zero-Trust Invariant

All external inputs are treated as **100% untrusted**:
- Model / LLM generated tool calls
- Voice audio transcriptions
- User prompt inputs
- Workspace file contents
- Web search / external API responses
- Remote client requests

Only the Python backend policy engine (`PolicyEngine`, `safety_guard`, `action_manager`) possesses authority to evaluate permissions and grant execution effects.

---

## 2. Deployment Boundaries & Exposure

1. **Local Desktop Mode (Default)**:
   - FastAPI server binds to loopback (`127.0.0.1`).
   - CORS origin allowlist strictly restricted to `http://localhost:5173`, `http://127.0.0.1:5173`, and `tauri://localhost`.
2. **Remote Access Mode (Explicitly Configured)**:
   - Requires explicit network binding configuration.
   - Enforces Bearer token authentication on all endpoints.
   - Enforces object-level authorization across action IDs and workspace boundaries.

---

## 3. Threat Mitigation Matrix

| Threat Category | Primary Defense | Verification |
| :--- | :--- | :--- |
| **Command Injection** | `safety_guard` pattern classifier + `shlex` parsing in `safe_exec`. Shell chaining (`&&`, `\|\|`, `;`) blocked. | Rejected at boundary before process spawn. |
| **Path Traversal** | Path canonicalization (`os.path.realpath`) and workspace root boundary check (`Path(path).resolve().is_relative_to(ROOT)`). | Traversal attempts (`../`) rejected. |
| **Secret Access** | Direct access to `.env`, `credentials`, private keys blocked unconditionally. | Prohibited path match rejected by policy. |
| **Prompt / Tool Injection** | LLM output parsed as structured data; unknown tools or permission escalations rejected by `ToolRegistry`. | Unknown tool error returned safely. |
| **Credential Leakage in Logs** | Structural field masking + regex pattern redaction in `sherly_core/observability.py`. | Secrets masked as `[REDACTED]`. |
| **Unauthorized Action Execution** | Server-authoritative `_pending_actions` queue with 120s TTL and single-use pop semantics. | Duplicate or expired approvals rejected. |
