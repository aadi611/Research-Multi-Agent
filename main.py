"""Multi-Agent Research Assistant with a live workflow control room."""
import os
import re
import tempfile
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Research Multi-Agent Control Room",
    page_icon="R",
    layout="wide",
    initial_sidebar_state="expanded",
)

STAGE_LABELS = {
    "cache": "Cache",
    "memory": "Memory",
    "plan": "Planning",
    "web": "Web Agent",
    "arxiv": "ArXiv Agent",
    "multimodal": "Multi-Modal Agent",
    "validate": "Validator",
    "report": "Report Builder",
}

STAGE_ORDER = [
    "cache",
    "memory",
    "plan",
    "web",
    "arxiv",
    "multimodal",
    "validate",
    "report",
]

st.markdown(
    """
<style>
:root {
    --ink: #102036;
    --muted: #42526e;
    --accent: #0d9488;
    --panel: #f7fbff;
    --edge: #c9d8ee;
    --flow: #1d4ed8;
    --flow-soft: #dbeafe;
    --good: #166534;
    --warn: #9a3412;
    --bad: #991b1b;
}

html, body, [class*="css"] {
    font-family: "Segoe UI", "Trebuchet MS", sans-serif;
}

.stApp {
    background:
      radial-gradient(900px 400px at -5% -15%, #dbeafe 0%, transparent 65%),
      radial-gradient(900px 500px at 110% -30%, #d1fae5 0%, transparent 55%),
      linear-gradient(180deg, #f8fbff 0%, #f3f6fb 100%);
}

.control-card {
    border: 1px solid var(--edge);
    background: white;
    border-radius: 14px;
    padding: 14px 16px;
    margin-bottom: 10px;
    box-shadow: 0 3px 10px rgba(15, 23, 42, 0.05);
}

.headline {
    color: var(--ink);
    font-weight: 700;
    letter-spacing: 0.2px;
    margin: 8px 0 2px;
}

.kpi-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    gap: 10px;
    margin-bottom: 12px;
}

.kpi-card {
    border: 1px solid var(--edge);
    border-radius: 12px;
    background: white;
    padding: 10px 12px;
}

.kpi-label {
    color: var(--muted);
    font-size: 0.8rem;
    font-weight: 600;
}

.kpi-value {
    color: var(--ink);
    font-size: 1.3rem;
    font-weight: 800;
}

.flow-wrap {
    border: 1px solid var(--edge);
    border-radius: 12px;
    background: white;
    padding: 12px;
    margin-bottom: 12px;
}

.flow-title {
    color: var(--ink);
    font-weight: 700;
    margin-bottom: 8px;
}

.flow-track {
    width: 100%;
    height: 12px;
    border-radius: 999px;
    background: #e7edf7;
    overflow: hidden;
    border: 1px solid #d7e2f2;
    margin: 6px 0 12px;
}

.flow-fill {
    height: 100%;
    width: 0%;
    border-radius: 999px;
    background: linear-gradient(90deg, #0ea5e9, #2563eb, #14b8a6);
    background-size: 180% 100%;
    animation: flowShift 1.7s linear infinite;
    transition: width 0.35s ease;
}

.graph-board {
    position: relative;
    border: 1px solid var(--edge);
    border-radius: 14px;
    background: linear-gradient(180deg, #f7fbff 0%, #f2f7ff 100%);
    min-height: 420px;
    overflow: hidden;
    margin-bottom: 12px;
}

.graph-title {
    position: absolute;
    top: 10px;
    left: 14px;
    color: var(--ink);
    font-size: 1.05rem;
    font-weight: 800;
}

.g-node {
    position: absolute;
    border: 2px solid #c9d8ee;
    border-radius: 12px;
    background: #ffffff;
    color: var(--ink);
    box-shadow: 0 4px 14px rgba(16, 32, 54, 0.08);
    padding: 10px;
}

.g-node.large {
    width: 270px;
    min-height: 96px;
}

.g-node.small {
    width: 150px;
    min-height: 80px;
}

.g-node.router {
    width: 140px;
    min-height: 90px;
}

.g-node-title {
    font-size: 0.95rem;
    font-weight: 800;
    line-height: 1.2;
}

.g-node-sub {
    font-size: 0.8rem;
    color: var(--muted);
    margin-top: 4px;
}

.g-dot {
    width: 10px;
    height: 10px;
    border-radius: 999px;
    display: inline-block;
    margin-right: 6px;
    background: #9ca3af;
}

.state-idle { border-color: #cbd5e1; background: #f8fafc; }
.state-idle .g-dot { background: #94a3b8; }

.state-running {
    border-color: #2563eb;
    background: #eff6ff;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.14), 0 4px 14px rgba(16, 32, 54, 0.1);
}
.state-running .g-dot { background: #2563eb; }

.state-completed { border-color: #16a34a; background: #f0fdf4; }
.state-completed .g-dot { background: #16a34a; }

.state-failed { border-color: #dc2626; background: #fef2f2; }
.state-failed .g-dot { background: #dc2626; }

.tool-node {
    position: absolute;
    width: 112px;
    min-height: 86px;
    border: 2px solid #c7d2fe;
    border-radius: 999px;
    background: #ffffff;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    box-shadow: 0 4px 10px rgba(37, 99, 235, 0.08);
    font-size: 0.78rem;
    color: var(--ink);
}

.tool-node .tool-label {
    margin-top: 4px;
    font-weight: 700;
    line-height: 1.1;
}

.edge {
    position: absolute;
    height: 3px;
    background: #8ea3c7;
    border-radius: 999px;
}

.edge.live {
    background: linear-gradient(90deg, #60a5fa, #2563eb, #22d3ee);
    background-size: 180% 100%;
    animation: flowShift 1.3s linear infinite;
}

.edge.dashed {
    height: 2px;
    background: transparent;
    border-top: 2px dashed #8ea3c7;
}

.edge-label {
    position: absolute;
    font-size: 0.72rem;
    color: #6b7280;
    font-weight: 700;
}

.graph-summary {
    margin-top: 6px;
    color: #42526e;
    font-size: 0.82rem;
}

.node-grid {
    display: grid;
    grid-template-columns: repeat(8, minmax(120px, 1fr));
    gap: 8px;
}

.node {
    border: 1px solid var(--edge);
    border-radius: 10px;
    background: var(--panel);
    padding: 8px;
    min-height: 74px;
    position: relative;
}

.node-name {
    color: var(--ink);
    font-size: 0.82rem;
    font-weight: 700;
}

.node-status {
    font-size: 0.74rem;
    font-weight: 700;
    margin-top: 4px;
}

.node-duration {
    color: var(--muted);
    font-size: 0.75rem;
    margin-top: 6px;
}

.node-idle { border-color: #d1d5db; background: #f8fafc; }
.node-running {
    border-color: #1d4ed8;
    background: #eff6ff;
    box-shadow: 0 0 0 2px rgba(29, 78, 216, 0.12) inset;
}
.node-completed { border-color: #16a34a; background: #f0fdf4; }
.node-failed { border-color: #dc2626; background: #fef2f2; }

.node-running::after {
    content: "";
    position: absolute;
    inset: -2px;
    border-radius: 11px;
    border: 2px solid rgba(29, 78, 216, 0.45);
    animation: pulseNode 1.2s ease-in-out infinite;
}

.node-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    color: #2563eb;
    font-weight: 900;
    font-size: 1.1rem;
}

.node-row {
    display: grid;
    grid-template-columns: repeat(15, minmax(30px, 1fr));
    gap: 6px;
    align-items: stretch;
}

.timeline-item {
    border-left: 3px solid var(--flow);
    margin: 8px 0;
    padding: 6px 10px;
    background: #f8faff;
    border-radius: 6px;
    color: var(--ink);
}

.stage-pill {
    border-radius: 999px;
    padding: 2px 10px;
    font-size: 0.75rem;
    font-weight: 700;
    display: inline-block;
    margin-left: 8px;
}

.timeline-item {
    border-left: 3px solid var(--flow);
}

.timeline-time {
    color: var(--muted);
    font-size: 0.78rem;
}

.agent-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(190px, 1fr));
    gap: 10px;
    margin-top: 8px;
}

.agent-card {
    border: 1px solid var(--edge);
    border-radius: 10px;
    padding: 10px;
    background: var(--panel);
}

@keyframes flowShift {
    0% { background-position: 0% 50%; }
    100% { background-position: 180% 50%; }
}

@keyframes pulseNode {
    0% { opacity: 0.9; transform: scale(1); }
    70% { opacity: 0.15; transform: scale(1.015); }
    100% { opacity: 0.9; transform: scale(1); }
}

@media (max-width: 1100px) {
    .node-row {
        grid-template-columns: repeat(8, minmax(100px, 1fr));
    }
    .node-arrow {
        display: none;
    }

    .graph-board {
        min-height: 560px;
    }

    .g-node.large, .g-node.small, .g-node.router, .tool-node {
        position: static;
        width: auto;
        margin: 8px;
        border-radius: 12px;
    }

    .edge, .edge-label, .graph-title {
        display: none;
    }
}
</style>
""",
    unsafe_allow_html=True,
)


def init_live_state() -> dict:
    return {
        "events": [],
        "stages": {k: {"status": "idle", "duration_s": None} for k in STAGE_ORDER},
        "active_stage": None,
        "run_start": None,
    }


def normalize_event(payload) -> dict:
    if isinstance(payload, dict):
        stage = payload.get("stage", "unknown")
        message = payload.get("message", "")
        status = payload.get("status", "info")
        timestamp = payload.get("timestamp", time.time())
        duration_s = payload.get("duration_s")
    else:
        stage, message = payload
        status = "info"
        timestamp = time.time()
        duration_s = None

    return {
        "stage": stage,
        "message": str(message),
        "status": status,
        "timestamp": float(timestamp),
        "duration_s": duration_s,
    }


def add_event(live_state: dict, payload) -> None:
    event = normalize_event(payload)
    live_state["events"].append(event)

    stage = event["stage"]
    if stage in live_state["stages"]:
        if event["status"] in {"running", "completed", "failed"}:
            live_state["stages"][stage]["status"] = event["status"]
        if event["duration_s"] is not None:
            live_state["stages"][stage]["duration_s"] = event["duration_s"]

    if event["status"] == "running":
        live_state["active_stage"] = stage
    if event["status"] in {"completed", "failed"} and live_state.get("active_stage") == stage:
        live_state["active_stage"] = None


def combine_status(statuses: list[str]) -> str:
    if any(s == "failed" for s in statuses):
        return "failed"
    if any(s == "running" for s in statuses):
        return "running"
    if statuses and all(s == "completed" for s in statuses):
        return "completed"
    if any(s == "completed" for s in statuses):
        return "running"
    return "idle"


def safe_report_filename(query: str) -> str:
    # Keep filename header-safe: one line, ASCII-ish, and compact.
    normalized = re.sub(r"\s+", "_", query.strip())
    normalized = re.sub(r"[^A-Za-z0-9._-]", "", normalized)
    normalized = normalized.strip("._-")
    if not normalized:
        normalized = "research"
    return f"research_{normalized[:40]}.md"


def render_control_room(live_state: dict, container):
    with container.container():
        total_events = len(live_state["events"])
        completed = sum(1 for s in live_state["stages"].values() if s["status"] == "completed")
        failed = sum(1 for s in live_state["stages"].values() if s["status"] == "failed")
        run_time = 0.0
        if live_state["run_start"]:
            run_time = time.time() - live_state["run_start"]

        current = STAGE_LABELS.get(live_state.get("active_stage"), "Idle")
        progress_pct = int((completed / len(STAGE_ORDER)) * 100)

        st.markdown("<div class='headline'>Execution Overview</div>", unsafe_allow_html=True)
        st.markdown(
            (
                "<div class='kpi-grid'>"
                f"<div class='kpi-card'><div class='kpi-label'>Run Time</div><div class='kpi-value'>{run_time:.1f}s</div></div>"
                f"<div class='kpi-card'><div class='kpi-label'>Completed</div><div class='kpi-value'>{completed}/{len(STAGE_ORDER)}</div></div>"
                f"<div class='kpi-card'><div class='kpi-label'>Active Node</div><div class='kpi-value'>{current}</div></div>"
                f"<div class='kpi-card'><div class='kpi-label'>Failures</div><div class='kpi-value'>{failed}</div></div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        st.markdown("<div class='headline'>Functional Workflow Canvas</div>", unsafe_allow_html=True)

        stage_states = {k: live_state["stages"][k]["status"] for k in STAGE_ORDER}
        agent_status = combine_status(
            [
                stage_states["cache"],
                stage_states["memory"],
                stage_states["plan"],
                stage_states["web"],
                stage_states["arxiv"],
                stage_states["multimodal"],
            ]
        )
        router_status = stage_states["validate"]
        response_status = stage_states["report"]
        fallback_status = "failed" if failed > 0 else ("completed" if response_status == "completed" else "idle")

        cache_dur = live_state["stages"]["cache"].get("duration_s")
        plan_dur = live_state["stages"]["plan"].get("duration_s")
        agent_dur = "-"
        if isinstance(cache_dur, (int, float)) or isinstance(plan_dur, (int, float)):
            total_agent = (cache_dur or 0.0) + (plan_dur or 0.0)
            agent_dur = f"{total_agent:.2f}s"

        validation_hint = "Routing by validation"
        if live_state["events"]:
            for event in reversed(live_state["events"]):
                if event["stage"] == "validate":
                    validation_hint = event["message"][:40]
                    break

        web_tool = stage_states["web"]
        arxiv_tool = stage_states["arxiv"]
        mm_tool = stage_states["multimodal"]
        mem_tool = stage_states["memory"]

        edge_1 = "live" if agent_status == "running" else ""
        edge_2 = "live" if agent_status == "running" or router_status == "running" else ""
        edge_3 = "live" if response_status == "running" else ""
        edge_4 = "live" if fallback_status == "failed" else ""

        st.markdown(
            (
                "<div class='flow-wrap'>"
                "<div class='flow-title'>Flowing Status Bar</div>"
                "<div class='flow-track'>"
                f"<div class='flow-fill' style='width:{progress_pct}%;'></div>"
                "</div>"
                f"<div class='graph-summary'>{progress_pct}% workflow complete</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            (
                "<div class='graph-board'>"
                "<div class='graph-title'>Single Agent + Tools + Router</div>"

                f"<div class='edge {edge_1}' style='left:15%;top:116px;width:11%;'></div>"
                f"<div class='edge {edge_2}' style='left:49%;top:116px;width:10%;'></div>"
                f"<div class='edge {edge_3}' style='left:72%;top:92px;width:11%;transform:rotate(-22deg);transform-origin:left center;'></div>"
                f"<div class='edge {edge_4}' style='left:72%;top:138px;width:11%;transform:rotate(21deg);transform-origin:left center;'></div>"

                "<div class='edge-label' style='left:18%;top:98px;'>query</div>"
                "<div class='edge-label' style='left:52%;top:98px;'>route</div>"
                "<div class='edge-label' style='left:79%;top:66px;'>true</div>"
                "<div class='edge-label' style='left:79%;top:168px;'>false</div>"

                "<div class='g-node small state-completed' style='left:4%;top:74px;'>"
                "<div class='g-node-title'><span class='g-dot'></span>Webhook</div>"
                "<div class='g-node-sub'>Input Trigger</div>"
                "</div>"

                f"<div class='g-node large state-{agent_status}' style='left:26%;top:74px;'>"
                "<div class='g-node-title'><span class='g-dot'></span>Research Agent</div>"
                f"<div class='g-node-sub'>Planner + Parallel tools | Duration: {agent_dur}</div>"
                "<div class='g-node-sub'>"
                f"Web:{stage_states['web']} | ArXiv:{stage_states['arxiv']} | Vision:{stage_states['multimodal']}"
                "</div>"
                "</div>"

                f"<div class='g-node router state-{router_status}' style='left:61%;top:78px;'>"
                "<div class='g-node-title'><span class='g-dot'></span>Router</div>"
                f"<div class='g-node-sub'>{validation_hint}</div>"
                "</div>"

                f"<div class='g-node small state-{response_status}' style='left:84%;top:36px;'>"
                "<div class='g-node-title'><span class='g-dot'></span>Response A</div>"
                "<div class='g-node-sub'>Final Report</div>"
                "</div>"

                f"<div class='g-node small state-{fallback_status}' style='left:84%;top:170px;'>"
                "<div class='g-node-title'><span class='g-dot'></span>Response B</div>"
                "<div class='g-node-sub'>Fallback / Error</div>"
                "</div>"

                "<div class='edge dashed' style='left:31%;top:252px;width:10%;transform:rotate(-25deg);transform-origin:left center;'></div>"
                "<div class='edge dashed' style='left:39%;top:252px;width:9%;transform:rotate(-18deg);transform-origin:left center;'></div>"
                "<div class='edge dashed' style='left:47%;top:252px;width:9%;transform:rotate(-12deg);transform-origin:left center;'></div>"
                "<div class='edge dashed' style='left:55%;top:252px;width:9%;transform:rotate(-7deg);transform-origin:left center;'></div>"

                f"<div class='tool-node state-{web_tool}' style='left:23%;top:286px;'>"
                "<div>TOOL</div><div class='tool-label'>Web Search</div>"
                "</div>"

                f"<div class='tool-node state-{mem_tool}' style='left:36%;top:286px;'>"
                "<div>MEM</div><div class='tool-label'>Memory</div>"
                "</div>"

                f"<div class='tool-node state-{arxiv_tool}' style='left:49%;top:286px;'>"
                "<div>TOOL</div><div class='tool-label'>ArXiv</div>"
                "</div>"

                f"<div class='tool-node state-{mm_tool}' style='left:62%;top:286px;'>"
                "<div>TOOL</div><div class='tool-label'>Vision</div>"
                "</div>"

                "</div>"
            ),
            unsafe_allow_html=True,
        )

        st.markdown("<div class='headline'>Ordered Event Timeline</div>", unsafe_allow_html=True)
        if total_events == 0:
            st.caption("Waiting for execution events...")
        else:
            recent = live_state["events"][-24:]
            for event in recent:
                ts = datetime.fromtimestamp(event["timestamp"]).strftime("%H:%M:%S")
                label = STAGE_LABELS.get(event["stage"], event["stage"].title())
                marker = {
                    "running": "[RUN]",
                    "completed": "[DONE]",
                    "failed": "[FAIL]",
                }.get(event["status"], "[INFO]")
                st.markdown(
                    (
                        "<div class='timeline-item'>"
                        f"<div><strong>{marker} {label}</strong> - {event['message']}</div>"
                        f"<div class='timeline-time'>{ts}</div>"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )


with st.sidebar:
    st.title("Research Console")
    st.caption("Real-time Multi-Agent Orchestration")

    st.subheader("Agents")
    st.markdown(
        "\n".join(
            [
                "- Web Research Agent",
                "- ArXiv Research Agent",
                "- Multi-Modal Agent",
                "- Validator + Report Builder",
            ]
        )
    )

    st.subheader("API")
    key_status = "Configured" if os.getenv("OPENAI_API_KEY") else "Missing"
    st.write(f"OPENAI_API_KEY: {key_status}")
    st.caption("Set this in `.env` or your system environment. It is not editable in the UI.")

    st.subheader("Visual Inputs (Optional)")
    image_urls_input = st.text_area(
        "Image URLs (one per line)",
        placeholder="https://example.com/chart.png",
        height=90,
    )
    uploaded_images = st.file_uploader(
        "Upload images",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png", "webp", "gif"],
    )

    if st.button("Clear Cache", use_container_width=True):
        if "orchestrator" in st.session_state:
            st.session_state.orchestrator.cache.clear()
            st.success("Cache cleared")

st.title("Research Multi-Agent Workflow")
st.caption("Run a query and watch each stage execute in real time.")

query = st.text_area(
    "Research Query",
    placeholder="What are the latest advances in quantum error correction?",
    height=100,
    label_visibility="collapsed",
)

run_col, _ = st.columns([1, 5])
with run_col:
    run_button = st.button("Run Research", type="primary", use_container_width=True)

control_room = st.empty()

if run_button:
    if not query.strip():
        st.warning("Please enter a research query.")
        st.stop()

    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is missing. Add it to `.env` (or system environment) and restart the app.")
        st.stop()

    image_urls = [u.strip() for u in image_urls_input.splitlines() if u.strip()]
    image_paths = []

    if uploaded_images:
        for uploaded in uploaded_images:
            suffix = os.path.splitext(uploaded.name)[1] or ".png"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
                f.write(uploaded.read())
                image_paths.append(f.name)

    with st.spinner("Initializing orchestrator..."):
        from src.orchestrator import ResearchOrchestrator

        # Recreate each run so code edits are reflected immediately.
        st.session_state.orchestrator = ResearchOrchestrator()

    orchestrator = st.session_state.orchestrator
    live_state = init_live_state()
    live_state["run_start"] = time.time()

    def progress_callback(event_or_stage, message: str = ""):
        payload = (
            event_or_stage
            if isinstance(event_or_stage, dict)
            else {"stage": event_or_stage, "message": message}
        )
        add_event(live_state, payload)
        render_control_room(live_state, control_room)

    render_control_room(live_state, control_room)

    try:
        result = orchestrator.run(
            query=query,
            image_urls=image_urls,
            image_paths=image_paths,
            progress_callback=progress_callback,
        )
    except Exception as e:
        st.error(f"Research failed: {e}")
        st.stop()

    render_control_room(live_state, control_room)

    for path in image_paths:
        try:
            os.remove(path)
        except OSError:
            pass

    if "error" in result:
        st.error(result["error"])
        st.stop()

    elapsed = time.time() - live_state["run_start"]
    st.success(f"Research complete in {elapsed:.1f}s using {result['agent_count']} agent(s).")

    st.markdown("---")
    st.header("Final Report")
    st.markdown(result["report"])

    st.markdown("---")
    st.header("Agent Findings")
    agent_tabs = st.tabs([r["agent"] for r in result["agent_results"]])
    for tab, agent_result in zip(agent_tabs, result["agent_results"]):
        with tab:
            st.markdown(agent_result.get("findings", "No findings"))
            if agent_result.get("papers"):
                st.subheader("Top Papers")
                for paper in agent_result["papers"]:
                    title = paper.get("title", "Untitled")
                    url = paper.get("url", "")
                    authors = ", ".join(paper.get("authors", []))
                    published = paper.get("published", "")
                    st.markdown(f"- [{title}]({url}) - {authors} ({published})")

    st.markdown("---")
    st.header("Validation")
    validation = result["validation"]
    st.write(f"Confidence: **{validation.get('confidence', 'unknown').title()}**")

    if validation.get("consistent_findings"):
        st.subheader("Consensus")
        for finding in validation["consistent_findings"]:
            st.markdown(f"- {finding}")

    if validation.get("has_contradictions") and validation.get("contradictions"):
        st.subheader("Resolved Contradictions")
        resolutions = result.get("resolutions", [])
        for i, contradiction in enumerate(validation["contradictions"]):
            with st.expander(f"Contradiction {i + 1}: {contradiction.get('topic', 'Unknown')}"):
                st.markdown(f"- Claim A: {contradiction.get('claim_a', 'N/A')}")
                st.markdown(f"- Claim B: {contradiction.get('claim_b', 'N/A')}")
                if i < len(resolutions):
                    st.markdown(f"- Resolution: {resolutions[i].get('resolution', 'N/A')}")

    with st.expander("Research Plan"):
        plan = result.get("plan", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Web Agent", "Active" if plan.get("use_web") else "Skipped")
        col2.metric("ArXiv Agent", "Active" if plan.get("use_arxiv") else "Skipped")
        col3.metric("Multi-Modal", "Active" if plan.get("use_multimodal") else "Skipped")
        st.caption(f"Rationale: {plan.get('rationale', 'N/A')}")

    st.download_button(
        "Download Report",
        data=result["report"],
        file_name=safe_report_filename(query),
        mime="text/markdown",
    )

else:
    idle_state = init_live_state()
    render_control_room(idle_state, control_room)
    st.caption("Run a query to animate node states and route decisions in real time.")
