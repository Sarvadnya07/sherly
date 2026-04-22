from runtime_utils import safe_execute
from tools.error_tools import analyze_error
from tools.fix_project import apply_last_fix, fix_project
from text_to_speech import speak

def handle_dev_command(low: str, raw: str, ask_model) -> str | None:
    if "explain error" in low or "analyze error" in low:
        return safe_execute(lambda: analyze_error(ask_model), "Failed to analyze the error.")

    if "fix my project" in low:
        speak("Running your project")
        return safe_execute(lambda: fix_project(ask_model), "Failed to run project fix workflow.")

    if "apply fix" in low:
        speak("Applying fix")
        result = safe_execute(lambda: apply_last_fix(ask_model), "Failed to apply project fix.")
        speak("Re-running project")
        return result
    
    return None
