import difflib
import uuid
import shutil
import os

from action_manager import log_action

preview_store = {}
backup_dir = "backups/"

def generate_diff(old: str, new: str) -> str:
    diff = difflib.unified_diff(
        old.splitlines(),
        new.splitlines(),
        lineterm=""
    )
    return "\n".join(diff)

def format_preview(change: dict, confidence: int = None, reason: str = "") -> str:
    diff = generate_diff(change["old"], change["new"])
    
    # Extract only additions and subtractions for inline preview
    lines = []
    for line in diff.split("\n"):
        if line.startswith("+") and not line.startswith("+++"):
            lines.append(f"➕ {line[1:100]}")
        elif line.startswith("-") and not line.startswith("---"):
            lines.append(f"➖ {line[1:100]}")
            
    clean = "\n".join(lines[:15]) # limit lines
    if len(lines) > 15:
        clean += "\n... (truncated)"
        
    out = f"📄 {change['file']}\n\nChange:\n{clean}"
    if reason:
        out += f"\n\nWhy: {reason}"
    if confidence is not None:
        out += f"\nConfidence: {confidence}%"
    return out

def generate_multi_diff(changes: list, confidence: int = None, reason: str = "") -> str:
    output = []
    for change in changes:
        output.append(format_preview(change, confidence, reason))
    return "\n\n────────────────\n\n".join(output)

def save_preview(action_id: str, changes: list):
    preview_store[action_id] = changes
    if len(preview_store) > 5:
        preview_store.pop(next(iter(preview_store)))

def backup_file(path: str) -> str:
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir, exist_ok=True)
    safe_name = path.replace("/", "_").replace("\\", "_").replace(":", "_")
    backup_path = os.path.join(backup_dir, safe_name)
    if os.path.exists(path):
        shutil.copy2(path, backup_path)
    return backup_path

def apply_preview(action_id: str) -> str:
    changes = preview_store.get(action_id)
    if not changes:
        return "Invalid preview ID"

    for change in changes:
        path = change["file"]
        old_code = change["old"]
        new_code = change["new"]

        backup_file(path)

        with open(path, "w", encoding="utf-8") as f:
            f.write(new_code)

        log_action(
            action=f"file_edit {path}",
            action_type="write_file",
            undo_data=("restore_file", path, old_code)
        )

    del preview_store[action_id]

    files = [os.path.basename(c["file"]) for c in changes]
    return f"Patch applied successfully to: {', '.join(files)}"
