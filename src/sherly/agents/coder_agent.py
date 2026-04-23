from sherly.agents.base_agent import BaseAgent

class CoderAgent(BaseAgent):
    def run(self, prompt: str, ask_model=None) -> str:
        if not ask_model:
            return "Error: no model provided."
        return ask_model(
            f"""
You are a coding expert.

Task:
{prompt}

Explain, fix, or improve code.
"""
        )

