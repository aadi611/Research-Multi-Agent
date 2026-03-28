"""Research Validator — detects and resolves contradictions across agent findings."""
import json
from openai import OpenAI


class ResearchValidator:
    def __init__(self, client: OpenAI, model: str = "gpt-5.4"):
        self.client = client
        self.model = model

    def validate(self, query: str, agent_results: list[dict]) -> dict:
        summaries = []
        for r in agent_results:
            summaries.append(f"[{r['agent']}]:\n{r.get('findings', 'No findings')[:1500]}")

        combined = "\n\n---\n\n".join(summaries)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Research Validator. Analyze findings from multiple agents for contradictions. Always respond with valid JSON only."},
                {"role": "user", "content": f"""Analyze these research findings for contradictions.

Research Topic: {query}

Agent Findings:
{combined}

Respond with this exact JSON (no markdown, raw JSON only):
{{
  "has_contradictions": true/false,
  "contradictions": [
    {{
      "topic": "what the contradiction is about",
      "claim_a": "first conflicting claim",
      "claim_b": "second conflicting claim",
      "agents_involved": ["agent names"]
    }}
  ],
  "consistent_findings": ["list of findings all agents agree on"],
  "confidence": "high/medium/low",
  "notes": "any other observations"
}}"""},
            ],
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {
                "has_contradictions": False,
                "contradictions": [],
                "consistent_findings": [],
                "confidence": "low",
                "notes": "Could not parse validation response.",
            }
