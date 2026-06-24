"""LLM client abstraction.

Production note: agents should depend on this interface instead of importing an SDK directly.
"""

from dataclasses import dataclass
from multi_agent_research_lab.core.config import get_settings


@dataclass(frozen=True)
class LLMResponse:
    content: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    cost_usd: float | None = None


class LLMClient:
    """Provider-agnostic LLM client skeleton."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        """Return a model completion.

        TODO(student): Connect OpenAI, Azure OpenAI, or another provider.
        Keep retry, timeout, and token logging here rather than inside agents.
        """
        if self.settings.openai_api_key:
            try:
                return self._complete_with_openai(system_prompt, user_prompt)
            except Exception:
                return self._mock_complete(system_prompt, user_prompt)
        return self._mock_complete(system_prompt, user_prompt)

    def _complete_with_openai(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        try:
            from openai import OpenAI
        except ImportError as exc:
            raise StudentTodoError(
                "OpenAI support requires the optional dependency `openai` to be installed."
            ) from exc

        client = OpenAI(api_key=self.settings.openai_api_key)
        response = client.chat.completions.create(
            model=self.settings.openai_model,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        usage = response.usage
        content = response.choices[0].message.content or ""
        input_tokens = None if usage is None else usage.prompt_tokens
        output_tokens = None if usage is None else usage.completion_tokens
        total_tokens = 0 if usage is None else usage.total_tokens
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=self._estimate_cost(total_tokens),
        )

    def _mock_complete(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        content = self._mock_content(system_prompt, user_prompt)
        input_tokens = max(1, (len(system_prompt) + len(user_prompt)) // 4)
        output_tokens = max(1, len(content) // 4)
        return LLMResponse(
            content=content,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            cost_usd=0.0,
        )

    def _mock_content(self, system_prompt: str, user_prompt: str) -> str:
        prompt = f"{system_prompt}\n{user_prompt}".lower()
        lines = [line.strip() for line in user_prompt.splitlines() if line.strip()]
        query = lines[0] if lines else user_prompt.strip()

        if "writer" in prompt or "final answer" in prompt:
            return (
                f"Final answer for '{query}':\n"
                "The topic benefits from a staged workflow: gather evidence, compare claims, then synthesize "
                "a concise answer. In practice, the best choice depends on whether quality and traceability "
                "outweigh added latency.\n\n"
                "Source references:\n"
                "- Use the collected research sources listed in the workflow output."
            )
        if "analyst" in prompt or "analysis" in prompt:
            return (
                "Key findings:\n"
                "- The sources converge on a common explanation of the topic.\n"
                "- Multi-step workflows improve structure but add latency and coordination cost.\n\n"
                "Comparison:\n"
                "- Baseline is faster.\n"
                "- Multi-agent is easier to inspect and debug.\n\n"
                "Weak evidence:\n"
                "- Some claims rely on summary snippets instead of full papers.\n\n"
                "Open questions:\n"
                "- Which evaluation rubric best matches the intended audience?"
            )
        if "researcher" in prompt or "research notes" in prompt:
            source_lines = [line for line in lines if line.startswith("[")]
            body = "\n".join(source_lines[:3]) if source_lines else "- No external sources were available."
            return f"Research notes for '{query}':\n{body}"
        if "single-agent" in prompt or "baseline" in prompt:
            return (
                f"Summary for: {query}\n\n"
                "This baseline response uses a single reasoning pass. It highlights the main topic, "
                "notes likely tradeoffs, and recommends validating claims with cited sources before use."
            )
        return f"Mock completion for: {query}"

    def _estimate_cost(self, total_tokens: int) -> float:
        # Placeholder estimate for lightweight benchmarking, not billing-grade accounting.
        return round(total_tokens * 0.0000005, 6)
