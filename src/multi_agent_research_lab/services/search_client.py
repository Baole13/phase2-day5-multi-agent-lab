"""Search client abstraction for ResearcherAgent."""

from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen
import json

from multi_agent_research_lab.core.config import get_settings
from multi_agent_research_lab.core.errors import StudentTodoError
from multi_agent_research_lab.core.schemas import SourceDocument


class SearchClient:
    """Provider-agnostic search client skeleton."""

    def __init__(self) -> None:
        self.settings = get_settings()

    def search(self, query: str, max_results: int = 5) -> list[SourceDocument]:
        """Search for documents relevant to a query.

        TODO(student): Implement with Tavily, Bing, SerpAPI, internal docs, or a local mock.
        """
        if self.settings.tavily_api_key:
            try:
                return self._search_tavily(query, max_results=max_results)
            except (HTTPError, URLError, TimeoutError, ValueError, KeyError):
                return self._mock_search(query, max_results=max_results)
        return self._mock_search(query, max_results=max_results)

    def _search_tavily(self, query: str, max_results: int) -> list[SourceDocument]:
        payload = json.dumps(
            {
                "query": query,
                "max_results": max_results,
                "search_depth": "basic",
                "include_answer": False,
            }
        ).encode("utf-8")
        request = Request(
            url="https://api.tavily.com/search",
            data=payload,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.settings.tavily_api_key}",
            },
            method="POST",
        )
        with urlopen(request, timeout=self.settings.timeout_seconds) as response:
            body = json.loads(response.read().decode("utf-8"))
        documents: list[SourceDocument] = []
        for item in body.get("results", [])[:max_results]:
            documents.append(
                SourceDocument(
                    title=item.get("title", "Untitled source"),
                    url=item.get("url"),
                    snippet=item.get("content", "")[:400],
                    metadata={"provider": "tavily"},
                )
            )
        return documents or self._mock_search(query, max_results=max_results)

    def _mock_search(self, query: str, max_results: int) -> list[SourceDocument]:
        slug = urlencode({"q": query}).split("=", maxsplit=1)[1]
        base_docs = [
            SourceDocument(
                title=f"Overview: {query}",
                url=f"https://example.com/research/{slug}",
                snippet=f"A high-level overview of {query}, including goals, tradeoffs, and common patterns.",
                metadata={"provider": "mock", "rank": 1},
            ),
            SourceDocument(
                title=f"Operational guide for {query}",
                url=f"https://example.com/guide/{slug}",
                snippet=f"Practical implementation notes for {query}, with emphasis on guardrails and workflows.",
                metadata={"provider": "mock", "rank": 2},
            ),
            SourceDocument(
                title=f"Evaluation notes on {query}",
                url=f"https://example.com/eval/{slug}",
                snippet=f"Suggested metrics and benchmarking ideas for {query}, including latency and quality tradeoffs.",
                metadata={"provider": "mock", "rank": 3},
            ),
        ]
        return base_docs[:max_results]
