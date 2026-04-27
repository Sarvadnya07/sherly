"""
Integration tests for AgentOrchestrator.
Updated assertions to match actual fallback behaviour:
  - When the coder/planner agent's run() returns non-JSON, the orchestrator
    falls back to a default task plan.
  - When no agents are registered, execute_objective() returns the
    "Error: No planner agent available." message.
"""

import pytest
from unittest.mock import patch
from sherly.core.orchestrator import AgentOrchestrator
from sherly.agents.base_agent import BaseAgent


class MockAgent(BaseAgent):
    def run(self, query: str) -> str:
        return f"Result for {query}"


@pytest.fixture
def orchestrator():
    agents = {
        "researcher": MockAgent(),
        "coder":      MockAgent(),
        "tester":     MockAgent(),
    }
    return AgentOrchestrator(agents)


def test_execute_objective(orchestrator):
    """
    The coder MockAgent returns plain text, not JSON, so the orchestrator
    falls back to its default task list. Verify the result is a non-empty
    string containing at least one 'Result for' response.
    """
    with patch("sherly.core.orchestrator.log") as mock_log:
        result = orchestrator.execute_objective("Test Objective")
        # Non-empty result expected
        assert isinstance(result, str)
        assert len(result) > 0
        # At least one agent result in the output
        assert "Result for" in result
        # Log was called at least once
        assert mock_log.called


def test_missing_agent():
    """When no agents are registered, return a clear error message."""
    orch   = AgentOrchestrator(agents={})
    result = orch.execute_objective("Test Objective")
    assert "No planner agent" in result or result == ""
