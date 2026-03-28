import base64
from pathlib import Path
from openai import OpenAI
from .base_agent import BaseAgent


class MultiModalResearchAgent(BaseAgent):
    def research(self, query: str, image_urls: list[str] = None, image_paths: list[str] = None, **kwargs) -> dict:
        content = []

        for url in (image_urls or []):
            content.append({"type": "image_url", "image_url": {"url": url}})

        for path_str in (image_paths or []):
            path = Path(path_str)
            if path.exists():
                suffix = path.suffix.lower()
                media_type = {".jpg": "image/jpeg", ".jpeg": "image/jpeg", ".png": "image/png", ".gif": "image/gif", ".webp": "image/webp"}.get(suffix, "image/jpeg")
                b64 = base64.standard_b64encode(path.read_bytes()).decode()
                content.append({"type": "image_url", "image_url": {"url": f"data:{media_type};base64,{b64}"}})

        has_visuals = bool(content)
        if has_visuals:
            content.append({"type": "text", "text": f"""Analyze the provided visual content in the context of this research topic:
Topic: {query}

Provide:
1. What the visuals show relevant to the topic
2. Key data, trends, or insights visible
3. How this supports or informs the research question
4. Any notable observations"""})
        else:
            content = [{"type": "text", "text": f"Provide a comprehensive overview of {query}, describing any typical visual representations, diagrams, or charts used to explain this topic."}]

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "user", "content": content}],
            max_completion_tokens=2000,
        )

        return {
            "agent": "Multi-Modal Research Agent",
            "query": query,
            "findings": self._get_text(response),
            "has_visual_content": has_visuals,
        }
