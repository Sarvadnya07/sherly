# Sherly Reliability, Observability & Performance Architecture (Phase 12)

**Target Scope**: System-wide Reliability, Diagnostics, Tracing, Metrics, and Performance  
**Classification**: High-Availability & Production Observability Layer  
**Status**: ACTIVE & PRODUCTION-READY  

---

## 1. Correlation & Trace Architecture

All incoming requests are assigned or inherit correlation identifiers at the API / WebSocket boundary:

```text
trace_id (Global session/request trace UUID)
 ├── request_id (Short 8-char transaction identity)
 ├── task_id (Background worker task ID)
 ├── action_id (Immutable human-in-the-loop action ID)
 └── voice_session_id (Active voice HUD correlation ID)
```

- **Propagation**: Propagated via HTTP response headers (`x-trace-id`, `x-request-id`) and structured JSON logs.
- **Privacy & Safety**: Private chain-of-thought or internal model prose is never exposed to public telemetry.

---

## 2. Structural & Pattern Secret Redaction

1. **Structural Redaction**: Dictionaries containing sensitive keys (`api_key`, `token`, `authorization`, `password`, `secret`, `private_key`) are masked with `[REDACTED]`.
2. **Regex Pattern Redaction**: String values are scanned for common token patterns (`sk-...`, `Bearer ...`, `AIza...`, `gsk_...`) and sanitized prior to serialization or logging.

---

## 3. Resilience & Fault Tolerance Layer

1. **Operation-Aware Retries**:
   - Transient network inquiries (e.g. cloud LLM queries, web searches) use exponential backoff with randomized jitter.
   - Non-idempotent operations (`filesystem.write`, `filesystem.delete`, `terminal.execute`, `action.approve`) are **never** blindly retried.
2. **Scoped Circuit Breakers**:
   - Circuit breakers are scoped per provider/operation (`ollama:generate`, `openai:models`).
   - States: `CLOSED` (normal) → `OPEN` (tripped after 3 consecutive errors; fast fails to fallback) → `HALF_OPEN` (probes recovery after cooldown).
3. **Graceful Shutdown**:
   - Releasing hardware audio streams (`sounddevice`, `pyttsx3`) and flushing logs cleanly on process termination.

---

## 4. Diagnostic Timeline Checkpoints

```text
request.received
       ↓
model.selected
       ↓
provider.request (with retry/circuit breaker if transient)
       ↓
tool.requested & policy check
       ↓
tool.started → tool.completed
       ↓
response.sent
```
