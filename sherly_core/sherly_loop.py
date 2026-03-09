from sherly_core.wake_word import SherlyWakeListener
from sherly_core.speech_to_text import transcribe
from sherly_core.intent_router import route_intent
from sherly_core import sherly_speak

listener = SherlyWakeListener()

def start_sherly():

    sherly_speak("Sherly is now online.")

    while True:

        listener.listen()

        sherly_speak("Yes?")

        command = transcribe()

        response = route_intent(command)

        sherly_speak(response)
