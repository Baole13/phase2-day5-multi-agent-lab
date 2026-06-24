"""Analyst agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class AnalystAgent(BaseAgent):
    """Turns research notes into structured insights."""

    name = "analyst"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.analysis_notes`.

        TODO(student): Extract key claims, compare viewpoints, and flag weak evidence.
        """
        research_notes = state.research_notes or "No research notes were available."
        with trace_span("analyst.run", {"query": state.request.query}) as span:
            response = self.llm_client.complete(
                system_prompt=(
                    "You are the Analyst agent. Convert research notes into structured findings with "
                    "key findings, comparison, weak evidence, and open questions."
                ),
                user_prompt=f"Query: {state.request.query}\n\nResearch notes:\n{research_notes}",
            )
            state.analysis_notes = response.content
            state.record_usage(
                mode="openai" if response.cost_usd else "mock",
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=response.cost_usd,
            )
            state.add_agent_result(
                AgentResult(
                    agent=AgentName.ANALYST,
                    content=response.content,
                    metadata={"had_research_notes": bool(state.research_notes)},
                )
            )
            span["attributes"]["had_research_notes"] = bool(state.research_notes)
            state.add_trace_event("analyst.completed", span)
            return state
