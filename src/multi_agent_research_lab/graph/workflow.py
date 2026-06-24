"""LangGraph workflow skeleton."""

from typing import Any

from multi_agent_research_lab.agents import AnalystAgent, ResearcherAgent, SupervisorAgent, WriterAgent
from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import AgentExecutionError
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span


class MultiAgentWorkflow:
    """Builds and runs the multi-agent graph.

    Keep orchestration here; keep agent internals in `agents/`.
    """

    def __init__(self) -> None:
        self.settings = get_settings()
        self.supervisor = SupervisorAgent()
        self.researcher = ResearcherAgent()
        self.analyst = AnalystAgent()
        self.writer = WriterAgent()

    def build(self) -> object:
        """Create a LangGraph graph.

        TODO(student): Implement nodes, edges, conditional routing, and stop condition.
        Suggested nodes: supervisor, researcher, analyst, writer, optional critic.
        """
        try:
            from langgraph.graph import END, START, StateGraph
        except ImportError:
            return {"type": "python-fallback", "nodes": ["supervisor", "researcher", "analyst", "writer"]}

        graph = StateGraph(ResearchState)
        graph.add_node("supervisor", self.supervisor.run)
        graph.add_node("researcher", self.researcher.run)
        graph.add_node("analyst", self.analyst.run)
        graph.add_node("writer", self.writer.run)
        graph.add_edge(START, "supervisor")
        graph.add_conditional_edges(
            "supervisor",
            self._next_route,
            {
                "researcher": "researcher",
                "analyst": "analyst",
                "writer": "writer",
                "done": END,
            },
        )
        graph.add_edge("researcher", "supervisor")
        graph.add_edge("analyst", "supervisor")
        graph.add_edge("writer", "supervisor")
        return graph

    def _next_route(self, state: ResearchState) -> str:
        return state.route_history[-1] if state.route_history else "done"

    def _run_python_fallback(self, state: ResearchState) -> ResearchState:
        while not state.completed:
            self.supervisor.run(state)
            route = state.route_history[-1]
            if route == "done":
                state.completed = True
                break
            if route == "researcher":
                self.researcher.run(state)
            elif route == "analyst":
                self.analyst.run(state)
            elif route == "writer":
                self.writer.run(state)
            else:
                raise AgentExecutionError(f"Unknown route returned by supervisor: {route}")
        return state

    def run(self, state: ResearchState) -> ResearchState:
        """Execute the graph and return final state.

        TODO(student): Compile graph, invoke it, and convert result back to ResearchState.
        """
        built = self.build()
        with trace_span("workflow.run", {"query": state.request.query}) as span:
            if isinstance(built, dict) and built.get("type") == "python-fallback":
                result = self._run_python_fallback(state)
            else:
                compiled = built.compile()
                result = compiled.invoke(state)
                if not isinstance(result, ResearchState):
                    result = ResearchState.model_validate(result)
            span["attributes"]["route_history"] = result.route_history
            result.add_trace_event("workflow.completed", span)
            return result
