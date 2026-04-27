"""
PROMPT OPTIMIZER — optimizer.py
Upgrades:
  FS-#25  RLHF-style prompt tuning pipeline:
           - analyze_performance() reads telemetry + Phase C feedback.
           - evolve_system_prompt() rewrites the active system prompt when
             success rate drops below threshold.
           - ab_test_prompt() runs a 100-query A/B test between current
             and candidate prompts, promotes the winner automatically.
"""

from __future__ import annotations

import json
import os
import random
import statistics
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from sherly.core.telemetry import TELEMETRY_FILE
from sherly.utils.runtime_utils import log


# ---------------------------------------------------------------------------
# Configurable thresholds
# ---------------------------------------------------------------------------
_SUCCESS_THRESHOLD    = 0.70   # Trigger prompt evolution below this rate
_AB_TEST_SAMPLE_SIZE  = 100    # Number of queries per A/B window
_EVOLVED_PROMPT_FILE  = Path("memory_rag") / "evolved_prompt.txt"


class PromptOptimizer:
    """
    Analyzes Phase C telemetry and feedback to evolve Sherly's system prompt.

    FS-#25: Full RLHF-style pipeline:
      1. analyze_performance() — assess success rate from telemetry + feedback
      2. evolve_system_prompt() — rewrite prompt when performance drops
      3. ab_test_prompt()       — compare candidate vs baseline over N queries
    """

    def __init__(self, telemetry_path: str = TELEMETRY_FILE) -> None:
        self.telemetry_path = telemetry_path

    # ------------------------------------------------------------------
    # 1. Performance analysis
    # ------------------------------------------------------------------

    def analyze_performance(self) -> dict[str, Any]:
        """
        FS-#25: Aggregate telemetry (self_heal events) + Phase C feedback log.
        Returns a performance summary dict.
        """
        success_count  = 0
        fail_count     = 0
        common_errors: dict[str, int] = {}
        feedback_pos   = 0
        feedback_neg   = 0

        # Source 1: telemetry.jsonl
        if os.path.exists(self.telemetry_path):
            try:
                with open(self.telemetry_path, "r", encoding="utf-8") as f:
                    for line in f:
                        try:
                            entry = json.loads(line.strip())
                        except json.JSONDecodeError:
                            continue
                        if entry.get("event_type") != "self_heal":
                            continue
                        data = entry.get("data", {})
                        if data.get("success"):
                            success_count += 1
                        else:
                            fail_count += 1
                            err = data.get("error", "unknown")[:80]
                            common_errors[err] = common_errors.get(err, 0) + 1
            except Exception as exc:
                log(f"[Optimizer] Telemetry read error: {exc}", level="error")

        # Source 2: feedback_log.jsonl (Phase C)
        feedback_candidates = [
            Path("feedback_log.jsonl"),
            Path(__file__).parent.parent / "logs" / "feedback_log.jsonl",
            Path("logs") / "feedback_log.jsonl",
        ]
        for p in feedback_candidates:
            if p.exists():
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        for line in f:
                            try:
                                entry = json.loads(line.strip())
                            except json.JSONDecodeError:
                                continue
                            rating = entry.get("rating", "").lower()
                            if rating == "y":
                                feedback_pos += 1
                            elif rating == "n":
                                feedback_neg += 1
                except Exception:
                    pass
                break

        total = success_count + fail_count
        feedback_total = feedback_pos + feedback_neg

        return {
            "success_rate":     success_count / total if total > 0 else 1.0,
            "fail_count":       fail_count,
            "success_count":    success_count,
            "common_errors":    common_errors,
            "feedback_positive": feedback_pos,
            "feedback_negative": feedback_neg,
            "feedback_rate":    feedback_pos / feedback_total if feedback_total > 0 else 1.0,
            "timestamp":        datetime.now(timezone.utc).isoformat(),
        }

    # ------------------------------------------------------------------
    # 2. Prompt evolution
    # ------------------------------------------------------------------

    def evolve_system_prompt(self) -> bool:
        """
        FS-#25: Rewrite the system prompt when success rate < threshold.
        Writes the evolved prompt to memory_rag/evolved_prompt.txt and
        returns True if evolution was triggered.
        """
        perf = self.analyze_performance()
        rate = min(perf["success_rate"], perf["feedback_rate"])

        if rate >= _SUCCESS_THRESHOLD:
            log(f"[Optimizer] Prompt OK (rate={rate:.2%}). No evolution needed.")
            return False

        log(
            f"[Optimizer] Performance below threshold ({rate:.2%} < {_SUCCESS_THRESHOLD:.0%}). "
            "Triggering prompt evolution...",
            level="warning",
        )

        top_errors = sorted(
            perf["common_errors"].items(), key=lambda x: x[1], reverse=True
        )[:5]
        error_hints = "\n".join(f"  - {e}" for e, _ in top_errors)

        evolved = (
            "You are Sherly, an autonomous developer AI assistant.\n"
            "Rules:\n"
            "- Answer naturally and directly.\n"
            "- Keep responses to 1-2 sentences unless detail is needed.\n"
            "- Never hallucinate facts. If unsure, say so.\n"
            "- Never execute DANGEROUS commands without explicit user approval.\n"
            "- Focus especially on: precise error log parsing and stack trace analysis.\n"
            f"- Known failure modes to avoid:\n{error_hints}\n"
        )

        _EVOLVED_PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
        _EVOLVED_PROMPT_FILE.write_text(evolved, encoding="utf-8")
        log(f"[Optimizer] Evolved prompt written to {_EVOLVED_PROMPT_FILE}")
        return True

    # ------------------------------------------------------------------
    # 3. A/B Testing
    # ------------------------------------------------------------------

    def ab_test_prompt(
        self,
        candidate_prompt: str,
        baseline_prompt: str,
        test_queries: list[str],
        ask_model_fn,
    ) -> str:
        """
        FS-#25: Run a simulated A/B test between candidate and baseline prompts
        over *test_queries*. Evaluates responses for length and confidence markers.

        Returns 'candidate' or 'baseline' (the winner).
        Writes the winning prompt to memory_rag/evolved_prompt.txt if candidate wins.
        """
        sample = random.sample(test_queries, min(_AB_TEST_SAMPLE_SIZE, len(test_queries)))

        baseline_scores:  list[float] = []
        candidate_scores: list[float] = []

        for query in sample:
            for prompt, scores in [
                (baseline_prompt,  baseline_scores),
                (candidate_prompt, candidate_scores),
            ]:
                try:
                    full_prompt = f"{prompt}\n\nUser: {query}"
                    response    = ask_model_fn(full_prompt, store_history=False, use_context=False)
                    # Simple heuristic score: longer + no "I don't know" = better
                    score = len(response)
                    if "i don't know" in response.lower() or "sorry" in response.lower():
                        score -= 200
                    scores.append(float(score))
                except Exception:
                    scores.append(0.0)

        baseline_mean  = statistics.mean(baseline_scores)  if baseline_scores  else 0.0
        candidate_mean = statistics.mean(candidate_scores) if candidate_scores else 0.0

        winner = "candidate" if candidate_mean > baseline_mean else "baseline"
        log(
            f"[Optimizer] A/B test complete — baseline={baseline_mean:.0f}, "
            f"candidate={candidate_mean:.0f}. Winner: {winner}"
        )

        if winner == "candidate":
            _EVOLVED_PROMPT_FILE.parent.mkdir(parents=True, exist_ok=True)
            _EVOLVED_PROMPT_FILE.write_text(candidate_prompt, encoding="utf-8")
            log(f"[Optimizer] Candidate prompt promoted → {_EVOLVED_PROMPT_FILE}")

        return winner

    def load_active_prompt(self) -> str | None:
        """Return the evolved prompt if one exists, else None (use default)."""
        if _EVOLVED_PROMPT_FILE.exists():
            return _EVOLVED_PROMPT_FILE.read_text(encoding="utf-8")
        return None
