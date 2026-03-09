from speech_to_text import transcribe
from text_to_speech import speak
from command_router import route_command


def main():
    speak("Sherly is online")

    try:
        while True:
            input("\nPress ENTER and speak...\n")

            text = transcribe()

            print("You:", text)

            if not text:
                continue

            response = route_command(text)

            print("Sherly:", response)

            speak(response)
    except KeyboardInterrupt:
        print("\nSherly shutting down.")


if __name__ == "__main__":
    main()
