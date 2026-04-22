from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def run(self, prompt: str, ask_model=None) -> str:
        """Execute the agent's main logic."""
        pass
        
    def stop(self) -> None:
        """Stop any ongoing operations."""
        pass
