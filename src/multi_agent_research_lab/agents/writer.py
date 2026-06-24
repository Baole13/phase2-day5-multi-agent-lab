"""Writer agent skeleton."""

from multi_agent_research_lab.agents.base import BaseAgent
from multi_agent_research_lab.core.schemas import AgentName, AgentResult
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.observability.tracing import trace_span
from multi_agent_research_lab.services.llm_client import LLMClient


class WriterAgent(BaseAgent):
    """Produces final answer from research and analysis notes."""

    name = "writer"

    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm_client = llm_client or LLMClient()

    def run(self, state: ResearchState) -> ResearchState:
        """Populate `state.final_answer`.

        TODO(student): Synthesize a clear response with citations or source references.
        """
        research_notes = state.research_notes or "Research notes were unavailable."
        analysis_notes = state.analysis_notes or "Analysis notes were unavailable."
        with trace_span("writer.run", {"query": state.request.query}) as span:
            response = self.llm_client.complete(
                system_prompt=(
                    "You are the Writer agent. Produce a concise final answer with a conclusion and short "
                    "source references. Acknowledge missing evidence instead of hallucinating details."
                ),
                user_prompt=(
                    f"Query: {state.request.query}\n\n"
                    f"Research notes:\n{research_notes}\n\n"
                    f"Analysis notes:\n{analysis_notes}"
                ),
            )
            answer = response.content
            if not state.research_notes or not state.analysis_notes:
                answer = (
                    "This answer was generated with limited upstream context.\n\n"
                    f"{response.content}"
                )
            state.final_answer = answer
            state.completed = True
            state.record_usage(
                mode="openai" if response.cost_usd else "mock",
                input_tokens=response.input_tokens,
                output_tokens=response.output_tokens,
                cost_usd=response.cost_usd,
            )
            state.add_agent_result(
                AgentResult(
                    agent=AgentName.WRITER,
                    content=answer,
                    metadata={"used_fallback_context": not (state.research_notes and state.analysis_notes)},
                )
            )
            span["attributes"]["used_fallback_context"] = not (state.research_notes and state.analysis_notes)
            state.add_trace_event("writer.completed", span)
            return state
