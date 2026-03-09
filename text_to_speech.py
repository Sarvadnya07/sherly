import pyttsx3


def speak(text):
    if not text:
        return

    text = text[:200]
    engine = pyttsx3.init()
    engine.setProperty("rate", 170)

    voices = engine.getProperty("voices")
    if len(voices) > 1:
        engine.setProperty("voice", voices[1].id)

    try:
        engine.say(text)
        engine.runAndWait()
        engine.stop()
    except Exception as exc:
        print("TTS ERROR:", exc)
