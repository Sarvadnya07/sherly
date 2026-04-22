import json
import os
from typing import List, Dict
from core.telemetry import TELEMETRY_FILE
from runtime_utils import log

class PromptOptimizer:
    """
    Analyzes telemetry to suggest prompt improvements.
    """
    def __init__(self, telemetry_path: str = TELEMETRY_FILE):
        self.telemetry_path = telemetry_path

    def analyze_performance(self) -> Dict[str, Any]:
        if not os.path.exists(self.telemetry_path):
            return {"status": "no_data"}
        
        success_count = 0
        fail_count = 0
        common_errors = {}

        try:
            with open(self.telemetry_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry["event_type"] == "self_heal":
                        data = entry["data"]
                        if data["success"]:
                            success_count += 1
                        else:
                            fail_count += 1
                            err = data.get("error", "unknown")
                            common_errors[err] = common_errors.get(err, 0) + 1
        except Exception:
            pass

        return {
            "success_rate": success_count / (success_count + fail_count) if (success_count + fail_count) > 0 else 1.0,
            "fail_count": fail_count,
            "common_errors": common_errors
        }

    def evolve_system_prompt(self):
        """
        Long-term vision: Recursive Self-Improvement.
        Automatically updates the system prompt based on performance.
        """
        perf = self.analyze_performance()
        if perf.get("success_rate", 1.0) < 0.7:
            log("[Optimizer] Success rate low. Triggering prompt evolution...")
            # Logic to rewrite system_prompt.txt or equivalent
            evolution_path = os.path.join(os.path.dirname(self.telemetry_path), "evolved_prompt.txt")
            with open(evolution_path, "w", encoding="utf-8") as f:
                f.write("REVISED_PROMPT: Focus more on specific error log parsing and stack trace analysis.")
            return True
        return False
