"""Main Orchestrator — coordinates all agents, memory, validation, and reporting."""
import os
import json
import time
import concurrent.futures
from typing import Callable
from openai import OpenAI

from .agents.web_agent import WebResearchAgent
from .agents.arxiv_agent import ArxivResearchAgent
from .agents.multimodal_agent import MultiModalResearchAgent
from .memory.cache import ResearchCache
from .memory.vector_store import ResearchVectorStore
from .validator import ResearchValidator
from .report_generator import ReportGenerator


class ResearchOrchestrator:
    def __init__(self, api_key: str = None):
        key = api_key or os.getenv("OPENAI_API_KEY")
        if not key:
            raise ValueError("OPENAI_API_KEY not set")

        self.client = OpenAI(api_key=key)
        self.model = "gpt-5.4"

        self.web_agent = WebResearchAgent(self.client, self.model)
        self.arxiv_agent = ArxivResearchAgent(self.client, self.model)
        self.multimodal_agent = MultiModalResearchAgent(self.client, self.model)

        self.cache = ResearchCache()
        self.vector_store = ResearchVectorStore()

        self.validator = ResearchValidator(self.client, self.model)
        self.report_gen = ReportGenerator(self.client, self.model)

    def plan_research(self, query: str) -> dict:
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a Research Planner. Respond with valid JSON only."},
                {"role": "user", "content": f"""Plan the research strategy for this query: {query}

Respond with raw JSON only:
{{
  "use_web": true/false,
  "use_arxiv": true/false,
  "use_multimodal": false,
  "web_focus": "specific angle for web research",
  "arxiv_focus": "specific angle for academic research",
  "rationale": "brief explanation"
}}

Guidelines:
- use_arxiv=true for scientific, technical, medical, or academic topics
- use_web=true almost always
- use_multimodal=false unless query explicitly mentions images/charts"""},
            ],
            response_format={"type": "json_object"},
        )

        try:
            return json.loads(response.choices[0].message.content)
        except Exception:
            return {"use_web": True, "use_arxiv": True, "use_multimodal": False, "web_focus": query, "arxiv_focus": query, "rationale": "Default plan"}

    def run(
        self,
        query: str,
        image_urls: list[str] = None,
        image_paths: list[str] = None,
        progress_callback: Callable | None = None,
    ) -> dict:
        def emit(stage: str, msg: str, status: str = "info", meta: dict | None = None):
            if progress_callback:
                event = {
                    "stage": stage,
                    "message": msg,
                    "status": status,
                    "timestamp": time.time(),
                }
                if meta:
                    event.update(meta)
                try:
                    progress_callback(event)
                except TypeError:
                    # Backward compatibility for older callback signature.
                    progress_callback(stage, msg)

        # 1. Cache check
        emit("cache", "Checking research cache...", "running")
        cached = self.cache.get(query)
        if cached:
            emit("cache", "Found cached results", "completed", {"from_cache": True})
            return cached
        emit("cache", "No cached results found", "completed")

        # 2. Similar past research
        emit("memory", "Searching past research...", "running")
        similar = self.vector_store.query_similar(query, n_results=2)
        if similar:
            emit("memory", f"Found {len(similar)} related past research entries", "completed")
        else:
            emit("memory", "No similar past research entries", "completed")

        # 3. Plan
        emit("plan", "Planning research strategy...", "running")
        plan = self.plan_research(query)
        emit("plan", f"Strategy ready: {plan.get('rationale', 'Multi-agent approach')}", "completed")

        # 4. Run agents in parallel
        agent_results = []
        future_to_stage = {}
        start_times = {}

        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            if plan.get("use_web", True):
                stage = "web"
                emit(stage, "Web Research Agent starting", "running")
                start_times[stage] = time.time()
                future_to_stage[executor.submit(self.web_agent.research, query, focus=plan.get("web_focus", ""))] = stage

            if plan.get("use_arxiv", True):
                stage = "arxiv"
                emit(stage, "ArXiv Research Agent starting", "running")
                start_times[stage] = time.time()
                future_to_stage[executor.submit(self.arxiv_agent.research, plan.get("arxiv_focus", query))] = stage

            has_visuals = bool(image_urls or image_paths)
            if plan.get("use_multimodal", False) or has_visuals:
                stage = "multimodal"
                emit(stage, "Multi-Modal Agent starting", "running")
                start_times[stage] = time.time()
                future_to_stage[executor.submit(
                    self.multimodal_agent.research, query, image_urls=image_urls or [], image_paths=image_paths or []
                )] = stage

            for future in concurrent.futures.as_completed(future_to_stage):
                stage = future_to_stage[future]
                duration = round(time.time() - start_times.get(stage, time.time()), 2)
                try:
                    result = future.result(timeout=120)
                    agent_results.append(result)
                    emit(stage, f"{result['agent']} completed", "completed", {"duration_s": duration})
                except Exception as e:
                    emit(stage, f"{stage} agent error: {e}", "failed", {"duration_s": duration})

        if not agent_results:
            return {"error": "All agents failed", "query": query}

        # 5. Validate
        emit("validate", "Research Validator checking for contradictions...", "running")
        validation = self.validator.validate(query, agent_results)

        resolutions = []
        if validation.get("has_contradictions"):
            contradictions = validation.get("contradictions", [])
            emit("validate", f"Found {len(contradictions)} contradiction(s), resolving...", "running")
            for c in contradictions:
                desc = f"{c.get('topic')}: {c.get('claim_a')} vs {c.get('claim_b')}"
                resolutions.append(self.web_agent.resolve_contradiction(desc))
            emit("validate", "Contradictions resolved", "completed")
        else:
            emit("validate", "No contradictions found", "completed")

        # 6. Generate report
        emit("report", "Generating final research report...", "running")
        report = self.report_gen.generate(query, agent_results, validation, resolutions)
        emit("report", "Report complete", "completed")

        # 7. Persist
        result = {
            "query": query,
            "plan": plan,
            "agent_results": agent_results,
            "validation": validation,
            "resolutions": resolutions,
            "report": report,
            "agent_count": len(agent_results),
            "summary": report[:500],
        }

        self.cache.set(query, result)
        self.vector_store.store(query, result)

        return result
