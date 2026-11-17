
import json
import logging
from dataclasses import asdict, dataclass
from datetime import date
from typing import Any

import arxiv

from .base_agent import BaseAgent


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------

DEFAULT_MAX_RESULTS = 8
DEFAULT_PAPER_LIMIT = 5
MAX_RESULTS_LIMIT = 30
MAX_TOOL_ITERATIONS = 5
ABSTRACT_MAX_LENGTH = 600


# ---------------------------------------------------------------------
# Data Models
# ---------------------------------------------------------------------

@dataclass
class Paper:
    title: str
    authors: list[str]
    abstract: str
    url: str
    published: str
    categories: list[str]

    @classmethod
    def from_arxiv(cls, result: Any) -> "Paper":
        abstract = result.summary.strip()

        if len(abstract) > ABSTRACT_MAX_LENGTH:
            abstract = abstract[:ABSTRACT_MAX_LENGTH].rstrip() + "..."

        return cls(
            title=result.title,
            authors=[author.name for author in result.authors[:3]],
            abstract=abstract,
            url=result.entry_id,
            published=str(result.published.date()),
            categories=result.categories[:3],
        )


# ---------------------------------------------------------------------
# ArXiv Search Service
# ---------------------------------------------------------------------

class ArxivSearchService:
    """Handles communication with the ArXiv API."""

    def __init__(self):
        self.client = arxiv.Client()

    def search(
        self,
        query: str,
        max_results: int = DEFAULT_MAX_RESULTS,
    ) -> list[Paper]:

        if not query or not query.strip():
            raise ValueError("Search query cannot be empty.")

        max_results = max(
            1,
            min(max_results, MAX_RESULTS_LIMIT),
        )

        search = arxiv.Search(
            query=query.strip(),
            max_results=max_results,
            sort_by=arxiv.SortCriterion.Relevance,
        )

        try:
            return [
                Paper.from_arxiv(result)
                for result in self.client.results(search)
            ]

        except Exception:
            logger.exception(
                "ArXiv search failed for query: %s",
                query,
            )
            raise


# ---------------------------------------------------------------------
# OpenAI Tool Definition
# ---------------------------------------------------------------------

ARXIV_TOOL = {
    "type": "function",
    "function": {
        "name": "search_arxiv",
        "description": (
            "Search ArXiv for academic research papers. "
            "Returns paper titles, authors, abstracts, publication "
            "dates, categories, and links."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Academic research search query.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Number of papers to retrieve.",
                    "minimum": 1,
                    "maximum": MAX_RESULTS_LIMIT,
                },
            },
            "required": ["query"],
            "additionalProperties": False,
        },
    },
}


# ---------------------------------------------------------------------
# Research Agent
# ---------------------------------------------------------------------

class ArxivResearchAgent(BaseAgent):
    """
    Academic research agent powered by ArXiv and OpenAI.

    Responsibilities:
    - Search academic literature.
    - Retrieve relevant research papers.
    - Analyze findings.
    - Identify research trends.
    - Highlight open research questions.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.arxiv_service = ArxivSearchService()

    # -----------------------------------------------------------------
    # Tool Execution
    # -----------------------------------------------------------------

    def _execute_tool(self, tool_call, fallback_query: str) -> str:
        """Execute an OpenAI tool call safely."""

        if tool_call.function.name != "search_arxiv":
            return json.dumps({
                "error": "Unknown tool requested."
            })

        try:
            args = json.loads(tool_call.function.arguments)

            query = args.get("query", fallback_query)
            max_results = args.get(
                "max_results",
                DEFAULT_MAX_RESULTS,
            )

            if not isinstance(query, str) or not query.strip():
                raise ValueError("Invalid search query.")

            if isinstance(max_results, bool) or not isinstance(
                max_results, int
            ):
                raise ValueError("max_results must be an integer.")

            papers = self.arxiv_service.search(
                query=query,
                max_results=max_results,
            )

            return json.dumps(
                [asdict(paper) for paper in papers],
                indent=2,
            )

        except Exception as exc:
            logger.exception("Tool execution failed.")

            return json.dumps({
                "error": str(exc),
                "tool": tool_call.function.name,
            })

    # -----------------------------------------------------------------
    # Research Instructions
    # -----------------------------------------------------------------

    @staticmethod
    def _build_messages(query: str) -> list[dict]:
        system_prompt = """
You are an expert academic research analyst.

Your task is to investigate research topics using ArXiv.

Research guidelines:

1. Use the search_arxiv tool to discover relevant papers.
2. Search using multiple relevant queries when necessary.
3. Prioritize papers based on relevance and research contribution.
4. Never invent paper titles, authors, dates, or findings.
5. Distinguish established findings from emerging hypotheses.
6. Identify disagreements and limitations in existing research.

Your final response must contain:

## 1. Academic Findings
Summarize the key findings and emerging consensus.

## 2. Relevant Research Papers
For each paper include:
- Title
- Authors
- Publication date
- Research contribution
- Relevance to the query
- ArXiv URL

## 3. Recent Research Trends
Explain emerging methodologies, technologies, and directions.

## 4. Open Research Questions
Identify unresolved problems and research opportunities.

## 5. Overall Assessment
Provide a concise synthesis of the literature.
"""

        user_prompt = f"""
Research topic: {query}

Conduct an academic literature review using ArXiv.

Focus on relevant, high-quality research and provide
evidence-based conclusions.
"""

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

    # -----------------------------------------------------------------
    # Main Research Workflow
    # -----------------------------------------------------------------

    def research(self, query: str, **kwargs) -> dict:
        """Execute the complete academic research workflow."""

        if not query or not query.strip():
            raise ValueError("Research query cannot be empty.")

        query = query.strip()

        messages = self._build_messages(query)

        max_iterations = kwargs.get(
            "max_iterations",
            MAX_TOOL_ITERATIONS,
        )

        max_iterations = max(
            1,
            min(int(max_iterations), 10),
        )

        final_response = None

        for iteration in range(max_iterations):

            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[ARXIV_TOOL],
                tool_choice="auto",
            )

            message = response.choices[0].message
            final_response = response

            if not message.tool_calls:
                break

            messages.append(message)

            for tool_call in message.tool_calls:
                result = self._execute_tool(
                    tool_call,
                    fallback_query=query,
                )

                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        else:
            logger.warning(
                "Maximum tool iterations reached for: %s",
                query,
            )

            # Ask the model to synthesize the available evidence.
            messages.append({
                "role": "user",
                "content": (
                    "Stop searching and synthesize the research "
                    "findings using the evidence already retrieved."
                ),
            })

            final_response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
            )

        # Retrieve papers only once for the final structured result.
        papers = self.arxiv_service.search(
            query=query,
            max_results=kwargs.get(
                "paper_limit",
                DEFAULT_PAPER_LIMIT,
            ),
        )

        findings = self._get_text(final_response)

        return {
            "agent": "ArXiv Research Agent",
            "query": query,
            "findings": findings,
            "papers": [
                asdict(paper)
                for paper in papers
            ],
            "metadata": {
                "total_papers": len(papers),
                "tool_iterations": iteration + 1,
                "generated_at": date.today().isoformat(),
            },
        }
