import requests
from config_manager import get_current_model

OLLAMA_URL = "http://localhost:11434/api/generate"


def ask_llm(prompt):
    model = get_current_model()

    if not model:
        return "No Ollama model is configured. Please ensure Ollama is running."

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False,
            },
        )
        response.raise_for_status()
        return response.json().get("response", "I'm having trouble thinking right now.")
    except Exception as e:
        return f"LLM Error: {e}"