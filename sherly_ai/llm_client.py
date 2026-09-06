from model_manager import ask_model


def ask_llm(prompt: str) -> str:
    """Unified LLM client interface delegating to model_manager."""
    if not prompt or not prompt.strip():
        return "Please specify a prompt."
    try:
        return ask_model(prompt, store_history=False, use_context=False)
    except Exception:
        return "I'm having trouble connecting to the model right now."