# Sherly AI — API & WebSocket Contracts Specification

**Version**: 2.0.0 (Phase 3 Hardened)  
**Protocol**: HTTP/1.1 REST & WebSocket  
**Format**: UTF-8 JSON  

---

## 1. REST Endpoints Matrix

### Chat & Memory
| Endpoint | Method | Request Body | Response Body | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/chat` | `POST` | `ChatRequest` (`prompt`, `file_attachment`) | `ChatResponse` (`user_prompt`, `assistant_response`, `timestamp`, `attached_file`, `request_id`) | `200`, `400`, `500` |
| `/api/chat/history` | `GET` | None | `ChatHistoryResponse` (`messages: ChatResponse[]`) | `200` |

### Models & Inference
| Endpoint | Method | Request Body | Response Body | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/models` | `GET` | None | `ModelsListResponse` (`mode`, `current_model`, `pinned_model`, `is_ollama_running`, `models`) | `200` |
| `/api/models/select` | `POST` | `ModelSelectRequest` (`model_name`) | `{ "message": str, "current_model": str }` | `200`, `400` |
| `/api/models/mode` | `POST` | `ModelModeRequest` (`mode: "auto" \| "manual"`) | `{ "mode": str, "current_model": str }` | `200`, `400` |
| `/api/models/refresh`| `POST` | None | `{ "count": int, "resolved": str }` | `200` |
| `/api/models/unload` | `POST` | None | `{ "message": str }` | `200` |
| `/api/models/key` | `POST` | `ApiKeyRequest` (`provider: "openai" \| "gemini" \| "groq"`, `api_key`) | `{ "message": str }` | `200`, `400` |

### Voice
| Endpoint | Method | Request Body | Response Body | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/voice/status` | `GET` | None | `VoiceStatusResponse` (`is_listening`, `is_speaking`, `current_device`) | `200` |
| `/api/voice/devices`| `GET` | None | `AudioDevicesResponse` (`devices: string[]`) | `200` |
| `/api/voice/start` | `POST` | None | `{ "message": str }` | `200` |
| `/api/voice/stop` | `POST` | None | `{ "message": str }` | `200` |

### Workspace & Files
| Endpoint | Method | Request Body | Response Body | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/files/tree` | `GET` | None | `FileNode` (`name`, `path`, `is_dir`, `children`) | `200` |
| `/api/files/read` | `GET` | Query `path` | `FileReadResponse` (`path`, `content`) | `200`, `403`, `404`, `413` |
| `/api/files/write` | `POST` | `FileWriteRequest` (`path`, `content`) | `{ "message": str }` | `200`, `403`, `500` |
| `/api/files/terminal/run` | `POST` | `TerminalRunRequest` (`command`) | `TerminalRunResponse` (`output`, `exit_code`) | `200`, `400` |

### Actions, Approvals & Previews
| Endpoint | Method | Request Body | Response Body | Status Codes |
| :--- | :--- | :--- | :--- | :--- |
| `/api/actions/approvals` | `GET` | None | `PendingApproval[]` (`action_id`, `command`, `level`, `timestamp`) | `200` |
| `/api/actions/approvals/{id}/approve` | `POST` | None | `{ "message": str }` | `200`, `404` |
| `/api/actions/approvals/{id}/reject` | `POST` | None | `{ "message": str }` | `200`, `404` |
| `/api/actions/history` | `GET` | None | `{ "history": ActionEntry[] }` | `200` |
| `/api/actions/undo` | `POST` | None | `{ "message": str }` | `200` |
| `/api/actions/previews/{id}` | `GET` | None | `PreviewChange[]` (`action_id`, `file_path`, `old_code`, `new_code`, `reason`) | `200`, `404` |
| `/api/actions/previews/{id}/apply` | `POST` | None | `{ "message": str }` | `200`, `404` |

---

## 2. WebSocket Real-Time Telemetry

* **Endpoint**: `ws://127.0.0.1:8000/ws`
* **Canonical Envelope**:
  ```json
  {
    "event_type": "status | stt_text | action_update | model_changed | pong",
    "payload": { ... },
    "timestamp": 1787150000.123,
    "request_id": "req_optional"
  }
  ```

### Event Types:
1. `status`: Broadcasts `{ "status": "ready" | "thinking" | "listening" | "speaking", "prompt": str }`
2. `stt_text`: Broadcasts real-time transcribed speech tokens `{ "text": str, "is_final": bool }`
3. `action_update`: Broadcasts approval / preview changes `{ "action_id": str, "status": "approved" | "rejected" | "preview_applied" }`
4. `model_changed`: Broadcasts model state updates `{ "current_model": str, "mode": "auto" | "manual" }`
5. `pong`: Heartbeat reply `{}`
