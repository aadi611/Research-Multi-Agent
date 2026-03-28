import json
import arxiv
from openai import OpenAI
from .base_agent import BaseAgent


def _search_arxiv(query: str, max_results: int = 8) -> str:
    client = arxiv.Client()
    search = arxiv.Search(
        query=query,
        max_results=max_results,
        sort_by=arxiv.SortCriterion.Relevance,
    )
    papers = []
    for result in client.results(search):
        papers.append({
            "title": result.title,
            "authors": [a.name for a in result.authors[:3]],
            "abstract": result.summary[:600] + "..." if len(result.summary) > 600 else result.summary,
            "url": result.entry_id,
            "published": str(result.published.date()),
            "categories": result.categories[:3],
        })
    return json.dumps(papers, indent=2)


ARXIV_TOOL = {
    "type": "function",
    "function": {
        "name": "search_arxiv",
        "description": "Search ArXiv for academic research papers. Returns titles, authors, abstracts, publication dates, and links.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "ArXiv search query"},
                "max_results": {"type": "integer", "description": "Number of papers to return (default 8)"},
            },
            "required": ["query"],
        },
    },
}


class ArxivResearchAgent(BaseAgent):
    def research(self, query: str, **kwargs) -> dict:
        messages = [
            {"role": "system", "content": "You are an academic research specialist. Use the search_arxiv tool to find relevant papers and summarize the academic consensus."},
            {"role": "user", "content": f"""Search ArXiv for papers about: {query}

Summarize:
1. Key academic findings and consensus
2. Most relevant papers (title + authors + why it's relevant)
3. Recent research trends
4. Open questions or debates in the literature"""},
        ]

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[ARXIV_TOOL],
                tool_choice="auto",
            )
            msg = response.choices[0].message

            if response.choices[0].finish_reason == "stop" or not msg.tool_calls:
                break

            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                result = _search_arxiv(args.get("query", query), args.get("max_results", 8))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return {
            "agent": "ArXiv Research Agent",
            "query": query,
            "findings": self._get_text(response),
            "papers": self._get_paper_list(query),
        }

    def _get_paper_list(self, query: str, max_results: int = 5) -> list[dict]:
        try:
            client = arxiv.Client()
            search = arxiv.Search(query=query, max_results=max_results, sort_by=arxiv.SortCriterion.Relevance)
            return [
                {"title": r.title, "authors": [a.name for a in r.authors[:3]], "url": r.entry_id, "published": str(r.published.date())}
                for r in client.results(search)
            ]
        except Exception:
            return []
