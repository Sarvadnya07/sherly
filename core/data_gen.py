import json
import os
from core.telemetry import TELEMETRY_FILE
from runtime_utils import log

class DatasetGenerator:
    """
    Generates fine-tuning datasets from successful self-healing sessions.
    """
    def __init__(self, telemetry_path: str = TELEMETRY_FILE):
        self.telemetry_path = telemetry_path
        self.dataset_path = "memory_rag/fine_tuning_data.jsonl"

    def export_successful_fixes(self):
        """
        Long-term vision: Synthetic Data Generation.
        Exports successful fixes as a dataset for local LLM fine-tuning.
        """
        if not os.path.exists(self.telemetry_path):
            return
            
        dataset = []
        try:
            with open(self.telemetry_path, "r", encoding="utf-8") as f:
                for line in f:
                    entry = json.loads(line)
                    if entry["event_type"] == "self_heal" and entry["data"]["success"]:
                        dataset.append({
                            "instruction": "Fix this error in the project.",
                            "input": entry["data"].get("error", ""),
                            "output": entry["data"].get("fix_applied", "Code modification applied successfully.")
                        })
            
            if dataset:
                os.makedirs(os.path.dirname(self.dataset_path), exist_ok=True)
                with open(self.dataset_path, "w", encoding="utf-8") as f:
                    for item in dataset:
                        f.write(json.dumps(item) + "\n")
                log(f"[DataGen] Exported {len(dataset)} training samples to {self.dataset_path}")
        except Exception as e:
            log(f"[DataGen] Export failed: {e}")
