import json
from typing import Dict
from sherly.agents.base_agent import BaseAgent
from sherly.utils.runtime_utils import log

class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents to solve complex objectives.
    """
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents

    def execute_objective(self, objective: str) -> str:
        log(f"[Orchestrator] Planning objective: {objective}")
        
        # 1. Plan the objective using the Coder agent or a specialized planner
        planner = self.agents.get("coder")
        if not planner:
            return "Error: No planner agent available."

        planning_prompt = f"""
You are the Orchestrator. Break down this objective into a series of tasks for specialized agents.
Available agents: {list(self.agents.keys())}

Objective: {objective}

Return strictly in JSON format:
{{
  "tasks": [
    {{ "agent": "agent_name", "task": "specific_task_description" }}
  ]
}}
"""
        plan_raw = planner.run(planning_prompt)
        
        try:
            # Simple cleanup of AI response
            if "```json" in plan_raw:
                plan_raw = plan_raw.split("```json")[1].split("```")[0].strip()
            elif "```" in plan_raw:
                plan_raw = plan_raw.split("```")[1].split("```")[0].strip()
            
            plan = json.loads(plan_raw)
            tasks = plan.get("tasks", [])
        except Exception:
            # Fallback to default tasks if planning fails
            tasks = [
                {"agent": "coder", "task": f"Analyze and implement: {objective}"},
                {"agent": "system", "task": f"Verify implementation of: {objective}"}
            ]
        
        results = []
        for t in tasks:
            agent_name = t.get("agent")
            task_desc = t.get("task")
            agent = self.agents.get(agent_name)
            if agent:
                log(f"[Orchestrator] Dispatching to {agent_name}: {task_desc}")
                res = agent.run(task_desc)
                results.append(f"### {agent_name.capitalize()} Result:\n{res}")
        
        return "\n\n".join(results)

def get_swarm_orchestrator():
    # Factory for orchestrator with default agents
    from sherly.agents.coder_agent import CoderAgent
    from sherly.agents.system_agent import SystemAgent
    from sherly.agents.browser_agent import BrowserAgent
    
    agents = {
        "coder": CoderAgent(),
        "system": SystemAgent(),
        "browser": BrowserAgent()
    }
    return AgentOrchestrator(agents)
