import webbrowser
import subprocess
import requests


def ask_llm(prompt):

    system_prompt = f"""
    You are Sherly, a desktop AI assistant.
    Answer the question in ONE short sentence.

    Question: {prompt}
    """

    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "mistral",
            "prompt": system_prompt,
            "stream": False
        }
    )

    return response.json()["response"]


def route_command(text):

    text = text.lower()

    # remove punctuation
    text = text.replace(",", " ")
    text = text.replace(".", " ")

    print("DEBUG ROUTER:", text)

    # youtube
    if "youtube" in text:
        webbrowser.open("https://youtube.com")
        return "Opening YouTube"

    # chrome
    if "chrome" in text:
        subprocess.Popen(
            "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        )
        return "Opening Chrome"

    # fallback
    return ask_llm(text)