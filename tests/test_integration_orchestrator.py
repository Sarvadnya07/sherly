import pytest
from unittest.mock import MagicMock, patch
from sherly.core.orchestrator import AgentOrchestrator
from sherly.agents.base_agent import BaseAgent

class MockAgent(BaseAgent):
    def run(self, query: str) -> str:
        return f"Result for {query}"

@pytest.fixture
def orchestrator():
    agents = {
        "researcher": MockAgent(),
        "coder": MockAgent(),
        "tester": MockAgent()
    }
    return AgentOrchestrator(agents)

def test_execute_objective(orchestrator):
    with patch("sherly.core.orchestrator.log") as mock_log:
        result = orchestrator.execute_objective("Test Objective")
        assert "Result for Research best practices for Test Objective" in result
        assert "Result for Implement the core logic for Test Objective" in result
        assert mock_log.called

def test_missing_agent(orchestrator):
    # Should not crash if an agent is missing
    orchestrator.agents = {}
    result = orchestrator.execute_objective("Test Objective")
    assert result == ""
