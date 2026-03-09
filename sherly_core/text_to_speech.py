from text_to_speech import speak as _root_speak

__all__ = ["speak", "sherly_speak"]


def speak(text):
    return _root_speak(text)


def sherly_speak(text):
    return _root_speak(text)
