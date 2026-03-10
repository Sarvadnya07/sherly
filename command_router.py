import webbrowser
import subprocess
import requests
import os
from datetime import datetime
from developer_tools import get_selected_text, explain_code

# --- Helper Functions ---

def ask_llm(prompt):
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "mistral",
                "prompt": f"You are Sherly, a desktop AI assistant. Max 2 sentences.\nUser: {prompt}",
                "stream": False
            }
        )
        return response.json().get("response", "I'm having trouble thinking right now.")
    except Exception as e:
        return f"LLM Error: {e}"

from text_to_speech import speak
from web_search import search_web

def needs_web_search(text):
    keywords = ["latest", "news", "today", "current", "recent", "price", "weather", "score", "who won"]
    return any(word in text for word in keywords)

def run_system_command(text):
    if "open github" in text or "github" in text:
        webbrowser.open("https://github.com")
        return "Opening GitHub"

    if "open chatgpt" in text:
        webbrowser.open("https://chat.openai.com")
        return "Opening ChatGPT"

    if "google" in text:
        webbrowser.open("https://google.com")
        return "Opening Google"

    if "youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    if "chrome" in text:
        try:
            subprocess.Popen("C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe")
            return "Opening Chrome"
        except FileNotFoundError:
            return "Chrome path not found."

    if "lock computer" in text:
        os.system("rundll32.exe user32.dll,LockWorkStation")
        return "Locking your computer"

    return None

# --- The Main Router ---

def route_command(text):
    # Clean the input
    text = text.lower().replace(",", "").replace(".", "").replace("?", "").strip()
    text = text.replace("sherly", "").strip()

    print("DEBUG ROUTER:", text)

    # 1. NEW: Developer Tools Logic (Inside the function!)
    if "explain this code" in text or "explain this" in text:
        code = get_selected_text()
        if not code:
            return "Please select or copy the code first."
        return explain_code(code, ask_llm)

    # 2. Check for system automation
    system_action = run_system_command(text)
    if system_action:
        return system_action

    # 3. Check for web search
    if needs_web_search(text):
        speak("Searching the web")
        results = search_web(text)
        if not results:
            return "I couldn't find anything online."
        
        context = "\n".join([f"{r['title']} - {r['body']}" for r in results[:3]])
        prompt = f"Use these results to answer: {text}\n\nResults:\n{context}"
        return ask_llm(prompt)

    # 4. Fallback to LLM
    return ask_llm(text)