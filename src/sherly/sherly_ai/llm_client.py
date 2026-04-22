import requests

OLLAMA_URL = "http://localhost:11434/api/generate"

def ask_llm(prompt):
    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": "mistral",
                "prompt": prompt,
                "stream": False
            }
        )
        response.raise_for_status()
        return response.json().get("response", "I'm having trouble thinking right now.")
    except Exception as e:
        return f"LLM Error: {e}"