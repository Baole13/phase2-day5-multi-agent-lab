from multi_agent_research_lab.agents import AnalystAgent, ResearcherAgent, SupervisorAgent, WriterAgent
from multi_agent_research_lab.core.schemas import ResearchQuery
from multi_agent_research_lab.core.state import ResearchState


def test_supervisor_routes_to_researcher_first() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "researcher"


def test_supervisor_stops_when_answer_exists() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        research_notes="notes",
        analysis_notes="analysis",
        final_answer="done",
    )
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "done"
    assert result.completed is True


def test_supervisor_falls_back_to_writer_on_iteration_limit() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"), iteration=99)
    result = SupervisorAgent().run(state)
    assert result.route_history[-1] == "writer"


def test_researcher_populates_sources_and_notes() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = ResearcherAgent().run(state)
    assert result.sources
    assert result.research_notes
    assert result.agent_results[-1].agent.value == "researcher"


def test_analyst_populates_analysis_notes() -> None:
    state = ResearchState(
        request=ResearchQuery(query="Explain multi-agent systems"),
        research_notes="Research notes for the topic.",
    )
    result = AnalystAgent().run(state)
    assert result.analysis_notes
    assert "Key findings" in result.analysis_notes


def test_writer_produces_fallback_answer_when_context_missing() -> None:
    state = ResearchState(request=ResearchQuery(query="Explain multi-agent systems"))
    result = WriterAgent().run(state)
    assert result.final_answer
    assert "limited upstream context" in result.final_answer
