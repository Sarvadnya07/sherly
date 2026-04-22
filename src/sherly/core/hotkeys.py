import keyboard
from sherly.utils.runtime_utils import log

class GlobalHotkeyManager:
    """
    Manages global hotkeys for Sherly AI.
    Default: Ctrl+Shift+S to toggle listening.
    """
    def __init__(self, toggle_callback):
        self.toggle_callback = toggle_callback
        self.hotkey = "ctrl+shift+s"

    def start(self):
        try:
            keyboard.add_hotkey(self.hotkey, self.on_hotkey_pressed)
            log(f"[Hotkeys] Registered global hotkey: {self.hotkey}")
        except Exception as e:
            log(f"[Hotkeys] Failed to register hotkey: {e}")

    def on_hotkey_pressed(self):
        log("[Hotkeys] Hotkey triggered!")
        if self.toggle_callback:
            self.toggle_callback()

    def stop(self):
        keyboard.unhook_all_hotkeys()
        log("[Hotkeys] Global hotkeys unhooked.")

def setup_hotkeys(ui_controller):
    """
    Helper to bind hotkeys to the UI listening state.
    """
    manager = GlobalHotkeyManager(toggle_callback=ui_controller.toggle_mic)
    manager.start()
    return manager
