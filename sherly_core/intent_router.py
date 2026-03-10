from sherly_commands.system_commands import run_system_command
from sherly_ai.llm_client import ask_llm

def route_intent(text):

    text = text.lower()

    # Pass the full text to system command handler which has its own routing logic
    result = run_system_command(text)
    if result:
        return result

    return ask_llm(text)