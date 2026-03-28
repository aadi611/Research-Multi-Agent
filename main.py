"""Multi-Agent Research Assistant with a live workflow control room."""
import os
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

        st.markdown("<div class='headline'>LangGraph-Style Pipeline</div>", unsafe_allow_html=True)

        node_html = []
        for idx, stage in enumerate(STAGE_ORDER):
            label = STAGE_LABELS[stage]
            stage_state = live_state["stages"][stage]
            status = stage_state["status"]
            dur = stage_state.get("duration_s")
            dur_text = f"{dur:.2f}s" if isinstance(dur, (float, int)) else "-"

            status_label = {
                "idle": "Idle",
                "running": "Running",
                "completed": "Completed",
                "failed": "Failed",
            }.get(status, "Info")

            status_color = {
                "idle": "#6b7280",
                "running": "#1d4ed8",
                "completed": "#15803d",
                "failed": "#b91c1c",
            }.get(status, "#374151")

            node_html.append(
                f"<div class='node node-{status}'>"
                f"<div class='node-name'>{label}</div>"
                f"<div class='node-status' style='color:{status_color};'>{status_label}</div>"
                f"<div class='node-duration'>Duration: {dur_text}</div>"
                "</div>"
            )
            if idx < len(STAGE_ORDER) - 1:
                node_html.append("<div class='node-arrow'>→</div>")

        st.markdown(
            (
                "<div class='flow-wrap'>"
                "<div class='flow-title'>Flowing Status Bar</div>"
                "<div class='flow-track'>"
                f"<div class='flow-fill' style='width:{progress_pct}%;'></div>"
                "</div>"
                f"<div style='color:#42526e;font-size:0.82rem;margin-bottom:10px;'>{progress_pct}% workflow complete</div>"
                f"<div class='node-row'>{''.join(node_html)}</div>"
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

    if "orchestrator" not in st.session_state:
        with st.spinner("Initializing orchestrator..."):
            from src.orchestrator import ResearchOrchestrator

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
        file_name=f"research_{query[:30].replace(' ', '_')}.md",
        mime="text/markdown",
    )

else:
    st.markdown("### Control Room Features")
    st.markdown(
        "\n".join(
            [
                "1. Ordered workflow timeline with timestamps.",
                "2. Live stage status (running/completed/failed).",
                "3. Active stage and run-time metrics.",
                "4. Agent findings, validation, and downloadable report.",
            ]
        )
    )
