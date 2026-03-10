from speech_to_text import transcribe
from text_to_speech import speak
from command_router import route_command


def start_sherly():

    speak("Sherly is online")

    while True:

        text = transcribe()

        if not text:
            continue

        print("You:", text)

        response = route_command(text)

        print("Sherly:", response)

        speak(response)
