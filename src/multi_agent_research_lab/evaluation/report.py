"""Benchmark report rendering."""

from multi_agent_research_lab.core.schemas import BenchmarkMetrics


def render_markdown_report(metrics: list[BenchmarkMetrics]) -> str:
    """Render benchmark metrics to markdown.

    TODO(student): Add richer analysis, examples, screenshots, and trace links.
    """

    lines = ["# Benchmark Report", "", "| Run | Latency (s) | Cost (USD) | Quality | Notes |", "|---|---:|---:|---:|---|"]
    for item in metrics:
        cost = "" if item.estimated_cost_usd is None else f"{item.estimated_cost_usd:.4f}"
        quality = "" if item.quality_score is None else f"{item.quality_score:.1f}"
        lines.append(f"| {item.run_name} | {item.latency_seconds:.2f} | {cost} | {quality} | {item.notes} |")
    if metrics:
        fastest = min(metrics, key=lambda item: item.latency_seconds)
        cheapest = min(metrics, key=lambda item: item.estimated_cost_usd or 0.0)
        lines.extend(
            [
                "",
                "## Summary",
                f"- Fastest run: `{fastest.run_name}` at {fastest.latency_seconds:.2f}s.",
                f"- Lowest estimated cost: `{cheapest.run_name}` at {(cheapest.estimated_cost_usd or 0.0):.4f} USD.",
                "- Failure mode notes: document missing citations, weak evidence, and fallback behavior here.",
            ]
        )
    return "\n".join(lines) + "\n"
