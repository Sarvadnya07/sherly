# Sherly Threat Model & Attack Surface Analysis (Phase 13)

**Classification**: STRIDE Threat Model & Defense-in-Depth Specification  
**Status**: ACTIVE & CERTIFIED  

---

## 1. Threat Classification (STRIDE)

| Threat | Surface | Attack Vector | Mitigation Strategy | Severity |
| :--- | :--- | :--- | :--- | :--- |
| **Spoofing** | API / WebSocket | Unauthorized client connects to local API. | Loopback binding + CORS restrict origin; Bearer token required in remote mode. | P2 |
| **Tampering** | File System / Actions | Malicious input attempts to alter action payload after approval. | Server-authoritative `_pending_actions` locks immutable command string. | P1 |
| **Repudiation** | Consequential Actions | User or agent performs state change without audit trail. | `action_manager.log_action()` records all state changes with UTC timestamp. | P2 |
| **Information Disclosure** | Logs & Errors | API key or credential printed in logs or UI traceback. | Structural + regex secret redaction in `sherly_core/observability.py`. | P0 |
| **Denial of Service** | LLM / Task Queue | Malicious rapid loop attempts to overwhelm LLM or queue. | Task queue size capped at 10; circuit breaker trips after 3 consecutive failures. | P1 |
| **Elevation of Privilege** | Tool Execution | Model proposes shell metacharacters or dangerous tool. | `safety_guard` blocks chaining; `PolicyEngine` enforces confirmation/block. | P0 |

---

## 2. Release Security Decision

- **P0 Findings Unresolved**: 0 (ZERO)
- **P1 Findings Unresolved**: 0 (ZERO)
- **P2 / P3 Hardening Notes**: Managed via local configuration guidelines and `.gitignore`.
- **Verdict**: **RELEASE READY**
