from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

class BasePlugin(ABC):
    """
    Standard SDK for Sherly AI Plugins.
    All plugins should inherit from this class.
    """
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The display name of the plugin."""
        pass

    @property
    def description(self) -> str:
        """A brief description of what the plugin does."""
        return ""

    @property
    def version(self) -> str:
        """The version of the plugin."""
        return "0.1.0"

    @abstractmethod
    def run(self, query: str) -> Any:
        """
        The main execution entry point for the plugin.
        """
        pass

    def on_load(self):
        """Called when the plugin is first loaded."""
        pass

    def on_unload(self):
        """Called when the plugin is disabled or unloaded."""
        pass
