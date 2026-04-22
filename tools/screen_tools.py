import mss
import pygetwindow as gw
from PIL import Image
import os
from datetime import datetime

def capture_screen(monitor_idx=None, region=None):
    """
    Capture screen. 
    monitor_idx: index of monitor to capture (1-based, 0 is all monitors combined)
    region: tuple (left, top, width, height)
    """
    with mss.mss() as sct:
        if region:
            monitor = region
        elif monitor_idx is not None:
            if monitor_idx < len(sct.monitors):
                monitor = sct.monitors[monitor_idx]
            else:
                monitor = sct.monitors[1]
        else:
            # Default to primary or all? Let's do primary.
            monitor = sct.monitors[1]
            
        screenshot = sct.grab(monitor)
        img = Image.frombytes("RGB", screenshot.size, screenshot.rgb)
        
        path = f"screen_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        img.save(path)
        return path

def analyze_screen(mode="active"):
    """
    mode: 'active' (active window), 'primary' (main monitor), 'all' (all monitors)
    """
    try:
        path = None
        if mode == "active":
            win = gw.getActiveWindow()
            if win:
                region = {"top": win.top, "left": win.left, "width": win.width, "height": win.height}
                path = capture_screen(region=region)
        
        if not path:
            path = capture_screen(monitor_idx=1 if mode == "primary" else 0)

        # Here we would call the model. Using a placeholder for the tool call logic.
        from model_manager import ask_model
        # Note: LLaVA or other vision models would be used here.
        # Since I'm an agent, I'll return the path and a note for the caller.
        return f"Captured {mode} screen at {path}. (Vision analysis would proceed with this file)"
    except Exception as e:
        return f"Failed to analyze screen: {e}"
