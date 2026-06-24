"""Supervisor / router skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.state import ResearchState


class SupervisorAgent(BaseAgent):
    """Decides which worker should run next and when to stop."""

    name = "supervisor"

    def __init__(self) -> None:
        self.settings = get_settings()

    def run(self, state: ResearchState) -> ResearchState:
        """Update `state.route_history` with the next route.

        TODO(student): Implement routing policy. Suggested steps:
        - Inspect request, current notes, and missing fields.
        - Choose one of: researcher, analyst, writer, done.
        - Enforce max iterations and failure fallback.
        """
        if state.completed or state.final_answer:
            route = "done"
            state.completed = True
        elif state.iteration >= self.settings.max_iterations or len(state.errors) >= 2:
            route = "writer"
        elif not state.research_notes:
            route = "researcher"
        elif not state.analysis_notes:
            route = "analyst"
        elif not state.final_answer:
            route = "writer"
        else:
            route = "done"
            state.completed = True

        state.record_route(route)
        state.add_trace_event(
            "supervisor.route",
            {
                "next": route,
                "iteration": state.iteration,
                "errors": len(state.errors),
                "completed": state.completed,
            },
        )
        return state
