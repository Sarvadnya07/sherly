import pystray
from PIL import Image
import threading

from sherly_core.sherly_loop import start_sherly

assistant_thread = None


def start_assistant(icon, item):

    global assistant_thread

    if assistant_thread is None:

        assistant_thread = threading.Thread(target=start_sherly)
        assistant_thread.daemon = True
        assistant_thread.start()

        print("Sherly started")


def stop_assistant(icon, item):

    print("Stop feature coming soon")


def exit_app(icon, item):

    icon.stop()


def create_tray():

    image = Image.new("RGB", (64, 64), color=(0, 120, 255))

    menu = pystray.Menu(
        pystray.MenuItem("Start Sherly", start_assistant),
        pystray.MenuItem("Exit", exit_app)
    )

    icon = pystray.Icon(
        "Sherly",
        image,
        "Sherly Assistant",
        menu
    )

    icon.run()
