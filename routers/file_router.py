from runtime_utils import safe_execute
from tools.file_tools import explain_file
from tools.project_tools import scan_project

def handle_file_command(low: str, raw: str, ask_model) -> str | None:
    if "open file" in low or "read file" in low:
        path = _extract_after(raw, "open file") or _extract_after(raw, "read file")
        if not path:
            return "Please specify a file path."
        return safe_execute(lambda: explain_file(path, ask_model), "Failed to open that file.")

    if "scan project" in low or "analyze project" in low:
        path = _extract_after(raw, "scan project") or _extract_after(raw, "analyze project")
        return safe_execute(lambda: scan_project(path, ask_model), "Failed to scan project.")
    
    return None

def _extract_after(raw: str, keyword: str) -> str:
    idx = raw.lower().find(keyword)
    if idx == -1:
        return ""
    return raw[idx + len(keyword):].strip(" \"'")
