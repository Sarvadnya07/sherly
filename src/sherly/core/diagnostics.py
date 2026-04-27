import requests
import psutil
import platform
import shutil
from typing import Dict, Any

class DiagnosticError(Exception):
    def __init__(self, message: str, component: str, context: Dict[str, Any] = None):
        super().__init__(message)
        self.component = component
        self.context = context or {}
        
def run_diagnostics() -> Dict[str, Any]:
    results = {"overall_health": "ok", "checks": {}, "hardware": {}}
    
    # 1. Check Ollama / LLM Backend
    try:
        res = requests.get("http://localhost:11434/api/tags", timeout=2)
        if res.status_code == 200:
            results["checks"]["ollama"] = "ok"
            models = res.json().get("models", [])
            results["checks"]["ollama_models"] = [m["name"] for m in models]
        else:
            results["checks"]["ollama"] = "degraded"
            results["overall_health"] = "degraded"
    except Exception as e:
        results["checks"]["ollama"] = f"error: {str(e)}"
        results["overall_health"] = "error"
        
    # 2. Hardware Telemetry
    # Memory
    mem = psutil.virtual_memory()
    total_gb = mem.total / (1024**3)
    available_gb = mem.available / (1024**3)
    results["hardware"]["memory"] = {
        "total_gb": round(total_gb, 2),
        "available_gb": round(available_gb, 2),
        "percent_used": mem.percent
    }
    
    # CPU
    results["hardware"]["cpu"] = {
        "cores": psutil.cpu_count(logical=False),
        "threads": psutil.cpu_count(logical=True),
        "usage_percent": psutil.cpu_percent(interval=0.1)
    }
    
    # Disk
    usage = shutil.disk_usage(".")
    results["hardware"]["disk"] = {
        "total_gb": round(usage.total / (1024**3), 2),
        "free_gb": round(usage.free / (1024**3), 2),
        "percent_used": round((usage.used / usage.total) * 100, 2)
    }

    # OS Info
    results["hardware"]["os"] = {
        "system": platform.system(),
        "release": platform.release(),
        "version": platform.version()
    }

    # 3. Pre-flight Warnings
    warnings = []
    if total_gb < 8.0:
        warnings.append("System RAM is below 8GB. Local LLMs may be slow or fail.")
    if available_gb < 2.0:
        warnings.append("Available RAM is very low (< 2GB). Expect performance issues.")
    if usage.free / (1024**3) < 5.0:
        warnings.append("Low disk space (< 5GB). Model downloads may fail.")
    
    if warnings:
        results["warnings"] = warnings
        if results["overall_health"] == "ok":
            results["overall_health"] = "warning"
            
    return results
