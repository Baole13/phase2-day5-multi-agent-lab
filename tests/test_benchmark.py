from multi_agent_research_lab.core.schemas import BenchmarkMetrics, ResearchQuery
from multi_agent_research_lab.core.state import ResearchState
from multi_agent_research_lab.evaluation.benchmark import run_benchmark
from multi_agent_research_lab.evaluation.report import render_markdown_report


def _runner(query: str) -> ResearchState:
    state = ResearchState(request=ResearchQuery(query=query))
    state.route_history = ["researcher", "analyst", "writer"]
    state.final_answer = "Done"
    state.completed = True
    state.usage["mode"] = "mock"
    return state


def test_benchmark_captures_latency_and_notes() -> None:
    _state, metrics = run_benchmark("multi-agent", "Explain multi-agent systems", _runner)
    assert metrics.latency_seconds >= 0
    assert "mode=mock" in metrics.notes


def test_report_renders_summary() -> None:
    report = render_markdown_report(
        [
            BenchmarkMetrics(run_name="baseline", latency_seconds=1.23, estimated_cost_usd=0.0),
            BenchmarkMetrics(run_name="multi-agent", latency_seconds=1.50, estimated_cost_usd=0.0),
        ]
    )
    assert "## Summary" in report
    assert "baseline" in report
