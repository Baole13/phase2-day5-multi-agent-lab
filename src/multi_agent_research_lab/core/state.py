"""Shared state for the multi-agent workflow.

Students should extend this file when adding new agents, outputs, or evaluation metrics.
"""

from typing import Any

from pydantic import BaseModel, Field

from multi_agent_research_lab.core.schemas import AgentResult, ResearchQuery, SourceDocument


class ResearchState(BaseModel):
    """Single source of truth passed through the workflow."""

    request: ResearchQuery
    iteration: int = 0
    route_history: list[str] = Field(default_factory=list)

    sources: list[SourceDocument] = Field(default_factory=list)
    research_notes: str | None = None
    analysis_notes: str | None = None
    final_answer: str | None = None

    agent_results: list[AgentResult] = Field(default_factory=list)
    trace: list[dict[str, Any]] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    usage: dict[str, float | int | str | None] = Field(
        default_factory=lambda: {
            "mode": "mock",
            "input_tokens": 0,
            "output_tokens": 0,
            "estimated_cost_usd": 0.0,
        }
    )
    completed: bool = False

    def record_route(self, route: str) -> None:
        self.route_history.append(route)
        self.iteration += 1

    def add_trace_event(self, name: str, payload: dict[str, Any]) -> None:
        self.trace.append({"name": name, "payload": payload})

    def add_agent_result(self, result: AgentResult) -> None:
        self.agent_results.append(result)

    def add_error(self, message: str) -> None:
        self.errors.append(message)

    def record_usage(
        self,
        *,
        mode: str | None = None,
        input_tokens: int | None = None,
        output_tokens: int | None = None,
        cost_usd: float | None = None,
    ) -> None:
        if mode is not None:
            self.usage["mode"] = mode
        if input_tokens is not None:
            self.usage["input_tokens"] = int(self.usage.get("input_tokens", 0)) + input_tokens
        if output_tokens is not None:
            self.usage["output_tokens"] = int(self.usage.get("output_tokens", 0)) + output_tokens
        if cost_usd is not None:
            self.usage["estimated_cost_usd"] = float(self.usage.get("estimated_cost_usd", 0.0)) + cost_usd
