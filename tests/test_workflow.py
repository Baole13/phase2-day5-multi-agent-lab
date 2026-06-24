from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.graph.workflow import MultiAgentWorkflow


def test_workflow_runs_end_to_end() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = MultiAgentWorkflow().run(state)
    assert result.final_answer
    assert "Final answer" in result.final_answer
    assert result.completed is True
    assert result.route_history[:3] == ["researcher", "analyst", "writer"]
    assert any(item["name"] == "workflow.completed" for item in result.trace)
