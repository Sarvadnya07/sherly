from typing import List, Dict, Any
from agents.base_agent import BaseAgent
from runtime_utils import log

class AgentOrchestrator:
    """
    Orchestrates multiple specialized agents to solve complex objectives.
    """
    def __init__(self, agents: Dict[str, BaseAgent]):
        self.agents = agents

    def execute_objective(self, objective: str) -> str:
        log(f"[Orchestrator] Planning objective: {objective}")
        # 1. Break objective into sub-tasks (Planning)
        # 2. Assign tasks to specialized agents
        # 3. Aggregate results
        
        # Example logic:
        tasks = [
            {"agent": "researcher", "task": f"Research best practices for {objective}"},
            {"agent": "coder", "task": f"Implement the core logic for {objective}"},
            {"agent": "tester", "task": f"Validate the implementation of {objective}"}
        ]
        
        results = []
        for t in tasks:
            agent = self.agents.get(t["agent"])
            if agent:
                log(f"[Orchestrator] Dispatching to {t['agent']}: {t['task']}")
                res = agent.run(t["task"])
                results.append(res)
        
        return "\n\n".join(results)

def get_swarm_orchestrator():
    # Factory for orchestrator with default agents
    from agents.coder_agent import CoderAgent
    from agents.system_agent import SystemAgent
    from agents.browser_agent import BrowserAgent
    
    agents = {
        "coder": CoderAgent(),
        "system": SystemAgent(),
        "browser": BrowserAgent()
    }
    return AgentOrchestrator(agents)
