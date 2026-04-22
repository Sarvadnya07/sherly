from typing import Any, Dict, Optional

class SherlyError(Exception):
    """Base exception for Sherly AI."""
    def __init__(self, message: str, code: str = "INTERNAL_ERROR", context: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.context = context or {}

class ActionError(SherlyError):
    """Raised when an action fails."""
    def __init__(self, message: str, action_id: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="ACTION_FAILED", context={"action_id": action_id, **(context or {})})

class EnvironmentError(SherlyError):
    """Raised when the environment is missing dependencies or hardware requirements."""
    def __init__(self, message: str, component: str, context: Optional[Dict[str, Any]] = None):
        super().__init__(message, code="ENV_ERROR", context={"component": component, **(context or {})})

class SecurityError(SherlyError):
    """Raised for prompt injection or unauthorized actions."""
    def __init__(self, message: str, risk_level: str = "high"):
        super().__init__(message, code="SECURITY_VIOLATION", context={"risk_level": risk_level})
