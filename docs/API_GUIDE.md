# Sherly AI — API & WebSocket Reference Guide

**Version**: 2.0.0  
**Base URL**: `http://127.0.0.1:8000`  

---

## 1. REST Endpoints

### Health & Observability
- **`GET /api/health`**: Returns application and memory health status.
- **`GET /api/health/providers`**: Returns local/cloud model provider availability.
- **`GET /api/health/diagnostics`**: Returns recent execution traces and timeline metrics.

### Action & Approval Control
- **`GET /api/actions/pending`**: List active actions awaiting approval (with remaining TTL).
- **`POST /api/actions/{action_id}/approve`**: Approve a pending action for execution.
- **`POST /api/actions/{action_id}/reject`**: Explicitly reject and cancel a pending action.
- **`POST /api/actions/undo`**: Revert the last supported file modification.

### Voice Operations
- **`POST /api/voice/stop_speaking`**: Immediately halts active audio playback and terminates TTS streams.
- **`GET /api/voice/devices`**: Returns list of available input audio capture devices.

---

## 2. WebSocket Real-Time Event Stream

**Endpoint**: `ws://127.0.0.1:8000/ws`

### Client Message Types
- `chat_message`: Send text prompt to the assistant (`{"type": "chat_message", "content": "..."}`).
- `cancel`: Abort current generation or tool execution (`{"type": "cancel"}`).

### Server Event Types
- `token`: Streaming text token chunk.
- `tool_call`: Live notification of capability invocation (`tool_name`, `args`).
- `approval_required`: Notification that an action requires explicit human confirmation.
- `complete`: Final response completed with execution timeline metrics.
