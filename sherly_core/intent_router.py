from sherly_commands.system_commands import run_system_command
from sherly_ai.llm_client import ask_llm

def route_intent(text):

    text = text.lower()

    if "open chrome" in text:
        return run_system_command("chrome")

    if "open vscode" in text:
        return run_system_command("vscode")

    if "shutdown computer" in text:
        return run_system_command("shutdown")

    if "visit chatgpt" in text:
        return run_system_command("chatgpt")

    return ask_llm(text)