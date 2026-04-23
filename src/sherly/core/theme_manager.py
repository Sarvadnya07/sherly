import os
import json
from pathlib import Path

class ThemeManager:
    """
    Theme Engine for Sherly AI.
    Manages QSS styles and color tokens.
    """
    
    DEFAULT_THEME = {
        "primary": "#00d2ff",
        "secondary": "#3a7bd5",
        "background": "rgba(20, 20, 25, 0.85)",
        "surface": "rgba(255, 255, 255, 0.05)",
        "text": "#ffffff",
        "text_muted": "#a0a0a0",
        "error": "#ff4d4d",
        "success": "#00ff88",
        "warning": "#ffcc00",
        "glass_blur": "20px",
        "border_radius": "12px"
    }

    def __init__(self, theme_path: str = "config/theme.json"):
        self.theme_path = Path(theme_path)
        self.theme_path.parent.mkdir(exist_ok=True)
        self.current_theme = self._load_theme()

    def _load_theme(self) -> dict:
        if not self.theme_path.exists():
            with open(self.theme_path, "w") as f:
                json.dump(self.DEFAULT_THEME, f, indent=4)
            return self.DEFAULT_THEME
        
        try:
            with open(self.theme_path, "r") as f:
                return {**self.DEFAULT_THEME, **json.load(f)}
        except Exception:
            return self.DEFAULT_THEME

    def generate_qss(self, template_path: str = "sherly_ui/assets/styles.qss.template") -> str:
        """
        Generates QSS by injecting theme tokens into a template.
        """
        template_file = Path(template_path)
        if not template_file.exists():
            return ""
        
        with open(template_file, "r") as f:
            qss = f.read()
            
        for key, value in self.current_theme.items():
            qss = qss.replace(f"@{key}", str(value))
            
        return qss

    def get_high_contrast_theme(self) -> dict:
        """Returns a high-contrast theme for better accessibility."""
        return {
            "primary": "#ffff00", # Bright yellow
            "secondary": "#00ffff", # Cyan
            "background": "#000000", # Pure black
            "surface": "#1a1a1a",
            "text": "#ffffff",
            "text_muted": "#ffffff",
            "error": "#ff0000",
            "success": "#00ff00",
            "warning": "#ffff00",
            "glass_blur": "0px", # No blur for performance/clarity
            "border_radius": "0px"
        }

    def set_accessibility_mode(self, enabled: bool):
        if enabled:
            self.update_theme(self.get_high_contrast_theme())
        else:
            self.update_theme(self.DEFAULT_THEME)
