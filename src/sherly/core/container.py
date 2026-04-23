from sherly.core.memory_rag import MemoryRAG
from sherly.services.action_manager import ActionManager
from sherly.services.model_manager import ask_model

class Container:
    """
    Simple Dependency Injection container for production-grade instance management.
    """
    _instances = {}

    @classmethod
    def get_memory_rag(cls) -> MemoryRAG:
        if "rag" not in cls._instances:
            cls._instances["rag"] = MemoryRAG()
        return cls._instances["rag"]

    @classmethod
    def get_action_manager(cls) -> ActionManager:
        if "action" not in cls._instances:
            cls._instances["action"] = ActionManager()
        return cls._instances["action"]

    @classmethod
    def get_model_fn(cls):
        return ask_model
