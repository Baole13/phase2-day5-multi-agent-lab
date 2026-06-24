"""Researcher agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient
from multi_agent_research_lab.services.search_client import SearchClient


class ResearcherAgent(BaseAgent):
    """Collects sources and creates concise research notes."""

    name = "researcher"

    def __init__(self, search_client: SearchClient | None = None, llm_client: LLMClient | None = None) -> None:
        self.search_client = search_client or SearchClient()
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.sources` and `state.research_notes`.

        TODO(student): Implement search, source filtering, citation capture, and notes.
        """
        with trace_span("researcher.run", {"query": state.request.query}) as span:
            sources = self.search_client.search(state.request.query, max_results=state.request.max_sources)
            source_lines = [
                f"[{index}] {source.title} - {source.snippet}"
                for index, source in enumerate(sources, start=1)
            ]
            response = self.llm_client.complete(
                system_prompt=(
                    "You are the Researcher agent. Turn source snippets into concise research notes "
                    "that preserve citations and uncertainty."
                ),
                user_prompt="\n".join([state.request.query, *source_lines]),
            )
            state.sources = sources
            state.research_notes = response.content
            state.record_usage(
                mode="openai" if response.cost_usd else "mock",
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=response.cost_usd,
            )
            state.add_agent_result(
                AgentResult(
                    agent=AgentName.RESEARCHER,
                    content=response.content,
                    metadata={"source_count": len(sources)},
                )
            )
            span["attributes"]["source_count"] = len(sources)
            state.add_trace_event("researcher.completed", span)
            return state
