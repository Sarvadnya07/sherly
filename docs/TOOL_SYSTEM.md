# Sherly AI — Generalized Capability & Tool System Specification

**Specification Level:** Canonical Production Architecture (Phase 4)  
**Principle:** "Capabilities, not hardcoded commands."  

---

## 1. Architectural Philosophy & Execution Flow

```
                      USER / NATURAL LANGUAGE
                                │
                                ▼
                       PLANNER / PARSER
                                │  (Structured JSON Tool Call)
                                ▼
                         TOOL REGISTRY
                                │  (Validation & Lookup)
                                ▼
                         POLICY ENGINE
            ┌───────────────────┴───────────────────┐
            │                                       │
         [SAFE]                      [CONFIRM / DANGEROUS]
            │                                       │
            │                               ACTION MANAGER
            │                                       │ (User Approval)
            ▼                                       ▼
    AUTHORIZED EXECUTOR (tools.terminal_tools / tools.file_tools / web_search)
                                │
                                ▼
                         STRUCTURED RESULT
                                │
                                ▼
                       FRONTEND / REST / WS
```

---

## 2. Canonical `ToolSpec` and `ToolResult`

### `ToolSpec`
Every tool in the system is defined by a strongly-typed `ToolSpec`:
- **`name`**: Namespaced capability identifier (`filesystem.read`, `terminal.execute`, `web.search`, etc.).
- **`description`**: Clear LLM-readable purpose.
- **`parameters_schema`**: JSON Schema of expected input arguments.
- **`handler`**: Python callable handler.
- **`risk`**: `SAFE` | `CONFIRM` | `DANGEROUS` | `BLOCKED`.
- **`permissions`**: Required permission scopes.
- **`requires_approval`**: Boolean flag indicating if approval is mandatory.
- **`reversible`**: Boolean flag indicating whether undo is supported.
- **`timeout`**: Timeout in seconds (default 30s).
- **`enabled`**: Activation flag.

### `ToolResult`
All tool executions produce a deterministic `ToolResult`:
```json
{
  "success": true,
  "tool": "filesystem.read",
  "output": "... contents ...",
  "error": null,
  "metadata": {
    "duration_ms": 42
  }
}
```

---

## 3. Registered Native Capabilities

| Tool Name | Risk Tier | Arguments | Description |
| :--- | :--- | :--- | :--- |
| `filesystem.read` | `SAFE` | `path: str` | Read workspace file contents. Blocked on `.env` / credentials. |
| `filesystem.scan` | `SAFE` | `path: Optional[str]` | Scan folder hierarchy and files. |
| `terminal.execute`| `CONFIRM` | `command: str` | Execute allowed CLI commands via prefix whitelist. |
| `web.search` | `SAFE` | `query: str` | Real-time web search via `ddgs`. |
| `browser.open` | `SAFE` | `url: str` | Open URL or media in user default browser. |
| `screen.capture` | `SAFE` | None | Capture screen for visual analysis. |

---

## 4. Policy & Security Enforcements

1. **Argument-Aware Safety**:
   - `filesystem.read` on `.env`, `id_rsa`, or credential paths is classified as `BLOCKED`.
   - `terminal.execute` inspects the command text: commands containing `rm -rf`, `format`, or `del` are classified as `DANGEROUS`/`BLOCKED`.
2. **Zero Shell Metacharacters**:
   - Command chaining (`&`, `;`, `|`, newline) is permanently blocked by `safe_exec`.
3. **No Execution of Free-Form Prose**:
   - The executor only processes structured `ToolSpec` invocations. Prose like `"Sure, I will delete..."` is never executed.
