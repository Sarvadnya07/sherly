import os

# Prevent Qt DPI warnings on some Windows setups
os.environ["QT_ENABLE_HIGHDPI_SCALING"] = "0"

from sherly_ui.app_manager import start_app

if __name__ == "__main__":
    start_app()
