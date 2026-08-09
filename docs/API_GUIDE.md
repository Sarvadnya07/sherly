# Internal API & Integration Guide

While Sherly is primarily a desktop application, it exposes several internal APIs and extension points (via the `plugins/` and `remote_api/` directories) to allow developers to build upon its orchestration engine.

## 🔌 Core Interfaces

### 1. The Tool Registry
To add a new deterministic capability to Sherly, register a function with `tool_registry.py`.

```python
from tool_registry import register_tool

@register_tool(name="restart_server", safety_level="CONFIRM")
def restart_server(context):
    """
    Restarts the local development server.
    """
    # implementation here
    pass
```

**Safety Levels:**
- `SAFE`: Executed immediately.
- `CONFIRM`: Will pause execution and prompt the PySide6 UI for user approval.
- `DANGEROUS`: Will be blocked unless the user has elevated developer mode active.

### 2. Action Manager (Patching)
If your custom tool or plugin needs to modify a file, **do not write to the file directly**. Use the Action Manager to ensure atomicity and reversibility.

```python
from action_manager import stage_patch

def my_custom_modifier(filepath, new_content):
    stage_patch(
        filepath=filepath,
        new_content=new_content,
        reason="Updated configuration via custom plugin."
    )
```

## 🌐 Remote API (Experimental)

Sherly contains a basic REST API (powered by FastAPI in `remote_api/`) to allow external tools (like a VSCode extension) to trigger Sherly commands.

### `POST /api/v1/command`
Execute a command as if it were typed in the UI.

**Request:**
```json
{
  "command": "scan the current directory",
  "source": "vscode_extension"
}
```

**Response:**
```json
{
  "status": "success",
  "action_id": "act_8291a",
  "requires_approval": false,
  "output": "Directory scanned. Found 12 files."
}
```

### Authentication
Currently, the REST API binds only to `localhost` (`127.0.0.1`). If exposed to a network, you must configure a Bearer token in `.env`:
`SHERLY_API_TOKEN=your_secure_token`
