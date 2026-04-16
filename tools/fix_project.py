import os
import uuid

from tools.error_fixer import analyze_error, generate_multi_fix
from tools.executor import run_project
from tools.project_detector import detect_project
from tools.preview import generate_multi_diff, save_preview

LAST_FIX_CONTEXT = {
    "lang": None,
    "command": None,
    "target_files": [],
    "error": None,
}


def _read_text(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    except Exception:
        return ""


def fix_project(ask_model):
    lang, command, target_file = detect_project()

    if not command:
        return "No project detected in the current folder."

    status, output = run_project(command)

    if status == "success":
        LAST_FIX_CONTEXT.update({"lang": lang, "command": command, "target_files": [target_file] if target_file else [], "error": None})
        return f"Detected {lang} project. Your project is running successfully."

    LAST_FIX_CONTEXT.update({
        "lang": lang,
        "command": command,
        "target_files": [target_file] if target_file else [],
        "error": output,
    })

    return (
        f"Detected {lang} project. Run command: `{command}`\n"
        f"Error detected.\n\n"
        f"Say 'apply fix' to let me calculate a fix and show a preview."
    )


def apply_last_fix(ask_model):
    command = LAST_FIX_CONTEXT.get("command")
    error = LAST_FIX_CONTEXT.get("error")
    target_files = LAST_FIX_CONTEXT.get("target_files", [])

    if not command or not error:
        return "No pending project error to fix. Say 'fix my project' first."

    if not target_files:
        return "I don't know which files to target for this project structure."

    files_context = ""
    for file_path in target_files:
        if os.path.exists(file_path):
            files_context += f"\n--- {file_path} ---\n{_read_text(file_path)[:3000]}\n"

    fix_data = generate_multi_fix(error, files_context, ask_model)

    if not fix_data or "changes" not in fix_data:
        return "I could not generate a valid code fix."

    confidence = fix_data.get("confidence", 0)
    reason = fix_data.get("reason", "No reason provided")
    changes = fix_data["changes"]

    if confidence < 60:
        return f"I found a potential fix, but confidence is too low ({confidence}%). I will not queue it.\n\nReason: {reason}"

    prepared_changes = []
    
    for change in changes:
        target_file = change["file"]
        new_code = change["new"]
        
        # Sometimes the AI tries to guess the relative path, resolve it explicitly if it matches a known file
        if not os.path.isabs(target_file):
            for t_file in target_files:
                if target_file in t_file:
                    target_file = t_file
                    break

        if not os.path.exists(target_file):
            continue

        original_code = _read_text(target_file)
        
        prepared_changes.append({
            "file": target_file,
            "old": original_code,
            "new": new_code,
        })
        
    if not prepared_changes:
        return "I generated a fix, but it targets files I cannot locate safely."

    diff_output = generate_multi_diff(prepared_changes, confidence, reason)
    action_id = str(uuid.uuid4())[:8]

    save_preview(action_id, prepared_changes)

    return f"""{diff_output}

Approve with: `approve {action_id}`"""
