import os
import requests
import psutil
from typing import Dict, Any

class DiagnosticError(Exception):
    def __init__(self, message: str, component: str, context: Dict[str, Any] = None):
        super().__init__(message)
        self.component = component
        self.context = context or {}
        
def run_diagnostics() -> Dict[str, Any]:
    results = {"overall_health": "ok", "checks": {}}
    
    # Check Ollama
    try:
        res = requests.get("http://localhost:11434/", timeout=2)
        if res.status_code == 200:
            results["checks"]["ollama"] = "ok"
        else:
            results["checks"]["ollama"] = "degraded"
            results["overall_health"] = "degraded"
    except Exception as e:
        results["checks"]["ollama"] = f"error: {str(e)}"
        results["overall_health"] = "error"
        
    # Check Memory
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024**3)
    available_gb = mem.available / (1024**3)
    results["checks"]["memory"] = {
        "total_gb": round(total_gb, 2),
        "available_gb": round(available_gb, 2)
    }
    if available_gb < 2.0:
        results["overall_health"] = "degraded"
        
    return results
