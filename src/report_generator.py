"""Generates the final comprehensive research report using OpenAI streaming."""
from openai import OpenAI


class ReportGenerator:
    def __init__(self, client: OpenAI, model: str = "gpt-5.4"):
        self.client = client
        self.model = model

    def generate(self, query: str, agent_results: list[dict], validation: dict, resolutions: list[dict] = None) -> str:
        agent_summaries = "\n\n".join(
            f"### {r['agent']}\n{r.get('findings', 'No findings')}"
            for r in agent_results
        )

        consistent = validation.get("consistent_findings", [])
        consistent_section = "\n**Points of Consensus:**\n" + "\n".join(f"- {f}" for f in consistent) if consistent else ""

        contradiction_section = ""
        if validation.get("has_contradictions") and resolutions:
            parts = []
            for i, (c, res) in enumerate(zip(validation.get("contradictions", []), resolutions)):
                parts.append(f"**Contradiction {i+1}** ({c.get('topic')}): {c.get('claim_a')} vs {c.get('claim_b')}\n**Resolution:** {res.get('resolution', 'N/A')}")
            contradiction_section = "\n\n### Resolved Contradictions\n" + "\n\n".join(parts)

        prompt = f"""You are a Research Report Generator. Synthesize the following multi-agent findings into a comprehensive report.

**Research Query:** {query}

**Agent Findings:**
{agent_summaries}
{consistent_section}
{contradiction_section}

**Validation Confidence:** {validation.get('confidence', 'unknown')}

Generate a professional research report with these sections:
1. **Executive Summary** (2-3 sentences)
2. **Key Findings** (bullet points)
3. **Academic Perspective** (from literature)
4. **Current State** (latest information)
5. **Analysis & Synthesis** (connect the dots)
6. **Conclusion** (direct answer to the query)
7. **Further Reading** (suggested next steps)

Use clear markdown formatting."""

        stream = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are an expert research synthesizer. Write clear, factual, well-structured reports."},
                {"role": "user", "content": prompt},
            ],
            max_completion_tokens=4000,
            stream=True,
        )

        parts = []
        for chunk in stream:
            delta = chunk.choices[0].delta.content
            if delta:
                parts.append(delta)
        return "".join(parts)
