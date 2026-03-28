import json
from openai import OpenAI
from .base_agent import BaseAgent


def _duckduckgo_search(query: str, max_results: int = 8) -> str:
    try:
        from duckduckgo_search import DDGS
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=max_results))
        return json.dumps(results, indent=2)
    except Exception as e:
        return json.dumps({"error": str(e)})


WEB_SEARCH_TOOL = {
    "type": "function",
    "function": {
        "name": "search_web",
        "description": "Search the web for current information using DuckDuckGo. Returns titles, snippets, and URLs.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query"},
                "max_results": {"type": "integer", "description": "Number of results (default 8)"},
            },
            "required": ["query"],
        },
    },
}


class WebResearchAgent(BaseAgent):
    def research(self, query: str, focus: str = "") -> dict:
        prompt = f"""Research the following topic thoroughly using web search.
Topic: {query}
{f"Focus: {focus}" if focus else ""}

Search for recent, credible information. Provide:
1. Key findings with sources/URLs
2. Current state of the topic
3. Important facts and data points
4. Any notable perspectives or debates"""

        messages = [
            {"role": "system", "content": "You are an expert web researcher. Use the search_web tool to gather comprehensive, current information."},
            {"role": "user", "content": prompt},
        ]

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[WEB_SEARCH_TOOL],
                tool_choice="auto",
            )
            msg = response.choices[0].message

            if response.choices[0].finish_reason == "stop":
                break

            if not msg.tool_calls:
                break

            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                result = _duckduckgo_search(
                    args.get("query", query),
                    args.get("max_results", 8),
                )
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return {
            "agent": "Web Research Agent",
            "query": query,
            "findings": self._get_text(response),
        }

    def resolve_contradiction(self, contradiction: str) -> dict:
        messages = [
            {"role": "system", "content": "You are a fact-checker. Use web search to find authoritative sources and resolve contradictions."},
            {"role": "user", "content": f"Resolve this contradiction using web search:\n\n{contradiction}\n\nFind the most accurate, up-to-date information."},
        ]

        while True:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                tools=[WEB_SEARCH_TOOL],
                tool_choice="auto",
            )
            msg = response.choices[0].message

            if response.choices[0].finish_reason == "stop" or not msg.tool_calls:
                break

            messages.append(msg)
            for tc in msg.tool_calls:
                args = json.loads(tc.function.arguments)
                result = _duckduckgo_search(args.get("query", contradiction[:100]))
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        return {"resolution": self._get_text(response)}
