import pyttsx3
import keyboard

_engine = None

def get_engine():
    global _engine
    if _engine is None:
        _engine = pyttsx3.init()
        _engine.setProperty("rate", 170)
        voices = _engine.getProperty("voices")
        if len(voices) > 1:
            # voices[1] is usually the female voice (Zira) on Windows
            _engine.setProperty("voice", voices[1].id)
    return _engine

def speak(text):
    if not text:
        return

    engine = get_engine()
    try:
        engine.say(text)
        engine.startLoop(False)

        while engine.isBusy():
            if keyboard.is_pressed("esc"):
                engine.stop()
                break
            engine.iterate()

        engine.endLoop()

    except Exception as exc:
        print("TTS ERROR:", exc)
        try:
            engine.endLoop()
        except:
            pass