from abc import ABC, abstractmethod

class BaseAgent(ABC):
    @abstractmethod
    def run(self, prompt: str, ask_model=None) -> str:
        pass

class IntentAgent(BaseAgent):
    """
    Agent focused on classifying user intent and routing.
    """
    @abstractmethod
    def classify(self, query: str) -> str:
        pass

class ToolAgent(BaseAgent):
    """
    Agent focused on executing specific technical tools (Coder, Browser, etc).
    """
    @abstractmethod
    def execute_tool(self, tool_name: str, args: dict) -> str:
        pass
