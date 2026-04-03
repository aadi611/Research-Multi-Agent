"""Production-style Streamlit UI for the multi-agent research assistant."""
import os
import re
import tempfile
import time
from datetime import datetime

import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Research Assistant Studio",
    page_icon="RS",
    layout="wide",
    initial_sidebar_state="expanded",
)

STAGE_LABELS = {
    "cache": "Cache",
    "memory": "Memory",
    "plan": "Planner",
    "web": "Web Agent",
    "arxiv": "ArXiv Agent",
    "multimodal": "Vision Agent",
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

PROMPT_TEMPLATES = [
    "Summarize the latest breakthroughs in fusion energy and list major technical bottlenecks.",
    "Compare open-source LLMs for on-device use in 2026 with tradeoffs on latency, quality, and memory.",
    "Tell me about the Strait of Hormuz and why it matters for global energy markets.",
    "What are the safest and most effective ways to improve sleep quality backed by recent studies?",
]

STATUS_META = {
    "idle": {"label": "Idle", "color": "#6b7280", "bg": "#f3f4f6"},
    "running": {"label": "Running", "color": "#1d4ed8", "bg": "#e0edff"},
    "completed": {"label": "Completed", "color": "#166534", "bg": "#dcfce7"},
    "failed": {"label": "Failed", "color": "#991b1b", "bg": "#fee2e2"},
}

st.markdown(
    """
<style>
:root {
  --ink: #0f223b;
  --muted: #475569;
  --soft: #eff6ff;
  --panel: #ffffff;
  --edge: #d7e3f3;
  --brand-a: #0ea5e9;
  --brand-b: #2563eb;
  --ok: #16a34a;
  --warn: #ea580c;
  --bad: #dc2626;
}

html, body, [class*="css"] {
  font-family: "Segoe UI", "Trebuchet MS", sans-serif;
}

.stApp {
  background:
    radial-gradient(900px 500px at -5% -20%, #dbeafe 0%, transparent 68%),
    radial-gradient(800px 500px at 110% -10%, #ccfbf1 0%, transparent 56%),
    linear-gradient(180deg, #f7fbff 0%, #f2f6fc 100%);
}

.topbar {
  border: 1px solid var(--edge);
  background: linear-gradient(120deg, #ffffff 0%, #f8fbff 100%);
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 10px;
}

.topbar-title {
  color: var(--ink);
  font-weight: 900;
  font-size: 1.25rem;
  letter-spacing: 0.2px;
}

.topbar-sub {
  color: var(--muted);
  font-size: 0.9rem;
}

.panel {
  border: 1px solid var(--edge);
  background: var(--panel);
  border-radius: 14px;
  padding: 14px;
  margin-bottom: 12px;
  box-shadow: 0 4px 14px rgba(15, 34, 59, 0.05);
}

.panel-title {
  color: var(--ink);
  font-weight: 800;
  margin-bottom: 8px;
}

.chat-wrap {
  max-height: 360px;
  overflow-y: auto;
  padding-right: 4px;
}

.msg {
  border-radius: 12px;
  padding: 10px 12px;
  margin: 8px 0;
  line-height: 1.45;
  border: 1px solid var(--edge);
}

.msg.user {
  background: #eef6ff;
  border-color: #bfdbfe;
}

.msg.assistant {
  background: #f8fafc;
}

.msg-role {
  font-size: 0.75rem;
  font-weight: 800;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 0.4px;
  margin-bottom: 5px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(145px, 1fr));
  gap: 8px;
  margin-bottom: 10px;
}

.kpi {
  border: 1px solid var(--edge);
  border-radius: 10px;
  background: #f9fbff;
  padding: 8px 10px;
}

.kpi-l {
  color: var(--muted);
  font-size: 0.74rem;
  font-weight: 700;
}

.kpi-v {
  color: var(--ink);
  font-size: 1.15rem;
  font-weight: 900;
}

.flow-track {
  width: 100%;
  height: 10px;
  border-radius: 999px;
  border: 1px solid #d3def0;
  background: #eaf0fa;
  overflow: hidden;
  margin: 6px 0 10px;
}

.flow-fill {
  height: 100%;
  width: 0%;
  border-radius: 999px;
  background: linear-gradient(90deg, var(--brand-a), var(--brand-b), #14b8a6);
  background-size: 180% 100%;
  animation: flowShift 1.6s linear infinite;
  transition: width 0.35s ease;
}

.stage-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}

.stage-card {
  border: 1px solid var(--edge);
  border-radius: 10px;
  background: #fff;
  padding: 8px;
}

.stage-name {
  color: var(--ink);
  font-size: 0.82rem;
  font-weight: 800;
}

.pill {
  display: inline-block;
  border-radius: 999px;
  padding: 2px 9px;
  font-size: 0.72rem;
  font-weight: 800;
  margin-top: 4px;
}

.stage-meta {
  color: var(--muted);
  font-size: 0.74rem;
  margin-top: 4px;
}

.canvas {
  position: relative;
  min-height: 230px;
  border: 1px solid var(--edge);
  background: linear-gradient(180deg, #f8fbff 0%, #f2f7ff 100%);
  border-radius: 12px;
  overflow: hidden;
  margin-top: 10px;
}

.node {
  position: absolute;
  border: 2px solid #cdd9ed;
  border-radius: 11px;
  background: #fff;
  padding: 8px;
  box-shadow: 0 3px 10px rgba(15, 34, 59, 0.05);
  color: var(--ink);
}

.node .t {
  font-size: 0.82rem;
  font-weight: 900;
}

.node .s {
  font-size: 0.73rem;
  color: var(--muted);
  margin-top: 3px;
}

.node.idle { border-color: #cbd5e1; background: #f8fafc; }
.node.running { border-color: #2563eb; background: #eff6ff; }
.node.completed { border-color: #16a34a; background: #f0fdf4; }
.node.failed { border-color: #dc2626; background: #fef2f2; }

.edge {
  position: absolute;
  height: 3px;
  border-radius: 999px;
  background: #8ea3c7;
}

.edge.live {
  background: linear-gradient(90deg, #60a5fa, #2563eb, #22d3ee);
  background-size: 170% 100%;
  animation: flowShift 1.2s linear infinite;
}

.event {
  border-left: 3px solid #1d4ed8;
  border-radius: 6px;
  background: #f8faff;
  padding: 6px 8px;
  margin: 7px 0;
}

.event-time {
  color: var(--muted);
  font-size: 0.72rem;
}

.small-muted {
  color: var(--muted);
  font-size: 0.8rem;
}

@keyframes flowShift {
  0% { background-position: 0% 50%; }
  100% { background-position: 180% 50%; }
}
</style>
""",
    unsafe_allow_html=True,
)


def init_live_state() -> dict:
    return {
        "events": [],
        "stages": {name: {"status": "idle", "duration_s": None} for name in STAGE_ORDER},
        "active_stage": None,
        "run_start": None,
    }


def init_session_state() -> None:
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Welcome. Ask a research question and I will orchestrate multiple agents.",
            }
        ]
    if "last_result" not in st.session_state:
        st.session_state.last_result = None
    if "live_state" not in st.session_state:
        st.session_state.live_state = init_live_state()
    if "run_history" not in st.session_state:
        st.session_state.run_history = []
    if "query_input" not in st.session_state:
        st.session_state.query_input = ""


def normalize_event(payload) -> dict:
    if isinstance(payload, dict):
        return {
            "stage": payload.get("stage", "unknown"),
            "message": str(payload.get("message", "")),
            "status": payload.get("status", "info"),
            "timestamp": float(payload.get("timestamp", time.time())),
            "duration_s": payload.get("duration_s"),
        }

    stage, message = payload
    return {
        "stage": stage,
        "message": str(message),
        "status": "info",
        "timestamp": time.time(),
        "duration_s": None,
    }


def add_event(live_state: dict, payload) -> None:
    event = normalize_event(payload)
    live_state["events"].append(event)

    stage = event["stage"]
    if stage in live_state["stages"]:
        if event["status"] in {"running", "completed", "failed"}:
            live_state["stages"][stage]["status"] = event["status"]
        if isinstance(event["duration_s"], (int, float)):
            live_state["stages"][stage]["duration_s"] = float(event["duration_s"])

    if event["status"] == "running":
        live_state["active_stage"] = stage
    if event["status"] in {"completed", "failed"} and live_state.get("active_stage") == stage:
        live_state["active_stage"] = None


def stage_status(live_state: dict, stage: str) -> str:
    return live_state["stages"].get(stage, {}).get("status", "idle")


def combine_status(values: list[str]) -> str:
    if any(v == "failed" for v in values):
        return "failed"
    if any(v == "running" for v in values):
        return "running"
    if values and all(v == "completed" for v in values):
        return "completed"
    if any(v == "completed" for v in values):
        return "running"
    return "idle"


def safe_report_filename(query: str) -> str:
    normalized = re.sub(r"\s+", "_", query.strip())
    normalized = re.sub(r"[^A-Za-z0-9._-]", "", normalized)
    normalized = normalized.strip("._-")
    if not normalized:
        normalized = "research"
    return f"research_{normalized[:40]}.md"


def record_run(query: str, live_state: dict, result: dict | None = None, error: str | None = None) -> None:
    duration = 0.0
    if live_state.get("run_start"):
        duration = round(time.time() - live_state["run_start"], 2)

    entry = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "query": query.strip(),
        "status": "failed" if error else "completed",
        "duration_s": duration,
        "agent_count": (result or {}).get("agent_count", 0),
        "error": error,
        "result": result,
    }

    st.session_state.run_history.insert(0, entry)
    st.session_state.run_history = st.session_state.run_history[:20]


def render_chat(messages: list[dict], container) -> None:
    with container.container():
        st.markdown("<div class='panel-title'>Conversation</div>", unsafe_allow_html=True)
        st.markdown("<div class='chat-wrap'>", unsafe_allow_html=True)
        for item in messages[-14:]:
            role = item.get("role", "assistant")
            content = item.get("content", "")
            role_text = "You" if role == "user" else "Assistant"
            st.markdown(
                (
                    f"<div class='msg {role}'>"
                    f"<div class='msg-role'>{role_text}</div>"
                    f"<div>{content}</div>"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )
        st.markdown("</div>", unsafe_allow_html=True)


def render_dashboard(live_state: dict, container, run_history: list[dict] | None = None) -> None:
    with container.container():
        completed_count = sum(1 for stage in STAGE_ORDER if stage_status(live_state, stage) == "completed")
        failed_count = sum(1 for stage in STAGE_ORDER if stage_status(live_state, stage) == "failed")
        progress = int((completed_count / len(STAGE_ORDER)) * 100)
        run_time = 0.0
        if live_state.get("run_start"):
            run_time = time.time() - live_state["run_start"]

        active = live_state.get("active_stage")
        active_label = STAGE_LABELS.get(active, "Idle")
        run_count = len(run_history or [])

        st.markdown("<div class='panel-title'>Agent Operations Dashboard</div>", unsafe_allow_html=True)

        st.markdown(
            (
                "<div class='kpi-grid'>"
                f"<div class='kpi'><div class='kpi-l'>Run Time</div><div class='kpi-v'>{run_time:.1f}s</div></div>"
                f"<div class='kpi'><div class='kpi-l'>Progress</div><div class='kpi-v'>{progress}%</div></div>"
                f"<div class='kpi'><div class='kpi-l'>Active Stage</div><div class='kpi-v'>{active_label}</div></div>"
                f"<div class='kpi'><div class='kpi-l'>Failures</div><div class='kpi-v'>{failed_count}</div></div>"
                f"<div class='kpi'><div class='kpi-l'>Total Runs</div><div class='kpi-v'>{run_count}</div></div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        st.markdown(
            (
                "<div class='flow-track'>"
                f"<div class='flow-fill' style='width:{progress}%;'></div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        stage_cards = []
        for stage in STAGE_ORDER:
            current = stage_status(live_state, stage)
            meta = STATUS_META.get(current, STATUS_META["idle"])
            duration = live_state["stages"][stage].get("duration_s")
            d_text = f"{duration:.2f}s" if isinstance(duration, (int, float)) else "-"
            stage_cards.append(
                (
                    "<div class='stage-card'>"
                    f"<div class='stage-name'>{STAGE_LABELS[stage]}</div>"
                    f"<span class='pill' style='color:{meta['color']};background:{meta['bg']};border:1px solid {meta['color']};'>{meta['label']}</span>"
                    f"<div class='stage-meta'>Duration: {d_text}</div>"
                    "</div>"
                )
            )

        st.markdown(f"<div class='stage-grid'>{''.join(stage_cards)}</div>", unsafe_allow_html=True)

        agent_state = combine_status(
            [
                stage_status(live_state, "cache"),
                stage_status(live_state, "memory"),
                stage_status(live_state, "plan"),
                stage_status(live_state, "web"),
                stage_status(live_state, "arxiv"),
                stage_status(live_state, "multimodal"),
            ]
        )
        router_state = stage_status(live_state, "validate")
        report_state = stage_status(live_state, "report")
        fallback_state = "failed" if failed_count else ("completed" if report_state == "completed" else "idle")

        edge_1 = "live" if agent_state == "running" else ""
        edge_2 = "live" if agent_state == "running" or router_state == "running" else ""
        edge_3 = "live" if report_state == "running" else ""
        edge_4 = "live" if fallback_state == "failed" else ""

        st.markdown(
            (
                "<div class='canvas'>"
                f"<div class='edge {edge_1}' style='left:14%;top:83px;width:13%;'></div>"
                f"<div class='edge {edge_2}' style='left:51%;top:83px;width:9%;'></div>"
                f"<div class='edge {edge_3}' style='left:72%;top:63px;width:10%;transform:rotate(-19deg);transform-origin:left center;'></div>"
                f"<div class='edge {edge_4}' style='left:72%;top:104px;width:10%;transform:rotate(19deg);transform-origin:left center;'></div>"
                "<div class='node completed' style='left:3%;top:45px;width:120px;'>"
                "<div class='t'>Webhook</div><div class='s'>Input Trigger</div>"
                "</div>"
                f"<div class='node {agent_state}' style='left:27%;top:40px;width:245px;'>"
                "<div class='t'>Research Agent + Tools</div><div class='s'>Plan + execute Web/ArXiv/Vision</div>"
                "</div>"
                f"<div class='node {router_state}' style='left:60%;top:45px;width:130px;'>"
                "<div class='t'>Router</div><div class='s'>Validation logic</div>"
                "</div>"
                f"<div class='node {report_state}' style='left:82%;top:20px;width:120px;'>"
                "<div class='t'>Response A</div><div class='s'>Final Report</div>"
                "</div>"
                f"<div class='node {fallback_state}' style='left:82%;top:114px;width:120px;'>"
                "<div class='t'>Response B</div><div class='s'>Fallback</div>"
                "</div>"
                "</div>"
            ),
            unsafe_allow_html=True,
        )

        st.markdown("<div class='panel-title' style='margin-top:8px;'>Event Stream</div>", unsafe_allow_html=True)
        recent = live_state["events"][-18:]
        if not recent:
            st.caption("Waiting for events...")
        else:
            for event in recent:
                ts = datetime.fromtimestamp(event["timestamp"]).strftime("%H:%M:%S")
                stage = STAGE_LABELS.get(event["stage"], event["stage"].title())
                marker = {
                    "running": "RUN",
                    "completed": "DONE",
                    "failed": "FAIL",
                }.get(event["status"], "INFO")
                st.markdown(
                    (
                        "<div class='event'>"
                        f"<div><strong>[{marker}] {stage}</strong> - {event['message']}</div>"
                        f"<div class='event-time'>{ts}</div>"
                        "</div>"
                    ),
                    unsafe_allow_html=True,
                )


def save_uploaded_images(files) -> list[str]:
    image_paths = []
    for uploaded in files or []:
        suffix = os.path.splitext(uploaded.name)[1] or ".png"
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(uploaded.read())
            image_paths.append(tmp.name)
    return image_paths


def cleanup_paths(paths: list[str]) -> None:
    for path in paths:
        try:
            os.remove(path)
        except OSError:
            pass


init_session_state()

with st.sidebar:
    st.title("Research Assistant")
    st.caption("Production Workflow Console")

    st.subheader("Configuration")
    key_status = "Configured" if os.getenv("OPENAI_API_KEY") else "Missing"
    st.write(f"OPENAI_API_KEY: {key_status}")
    st.caption("Set in `.env` or system environment. Hidden from UI.")

    st.subheader("Optional Inputs")
    image_urls_input = st.text_area(
        "Image URLs (one per line)",
        placeholder="https://example.com/chart.png",
        height=84,
    )
    uploaded_images = st.file_uploader(
        "Upload Images",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png", "webp", "gif"],
    )

    st.subheader("Quick Prompts")
    selected_prompt = st.selectbox(
        "Choose a starter prompt",
        options=["Custom"] + PROMPT_TEMPLATES,
        index=0,
        key="selected_prompt",
    )
    if st.button("Use Selected Prompt", use_container_width=True):
        if selected_prompt != "Custom":
            st.session_state.query_input = selected_prompt

    st.subheader("Run History")
    if st.session_state.run_history:
        history_labels = [
            f"{item['timestamp']} | {item['status'].upper()} | {item['query'][:44]}"
            for item in st.session_state.run_history
        ]
        selected_idx = st.selectbox(
            "Recent runs",
            options=list(range(len(history_labels))),
            format_func=lambda i: history_labels[i],
            key="history_idx",
        )
        picked = st.session_state.run_history[selected_idx]
        st.caption(f"Duration: {picked['duration_s']}s | Agents: {picked['agent_count']}")
        if picked.get("error"):
            st.caption(f"Error: {picked['error'][:120]}")
        if st.button("Load Selected Report", use_container_width=True):
            if picked.get("result"):
                st.session_state.last_result = picked["result"]
                st.session_state.chat_messages.append(
                    {"role": "assistant", "content": f"Loaded report from run at {picked['timestamp']}."}
                )
                st.rerun()
    else:
        st.caption("No runs yet.")

    if st.button("Clear Cache", use_container_width=True):
        if "orchestrator" in st.session_state:
            st.session_state.orchestrator.cache.clear()
            st.success("Cache cleared")

    if st.button("Clear Conversation", use_container_width=True):
        st.session_state.chat_messages = [
            {
                "role": "assistant",
                "content": "Conversation reset. Ask a new research question.",
            }
        ]
        st.session_state.last_result = None
        st.session_state.live_state = init_live_state()

st.markdown(
    (
        "<div class='topbar'>"
        "<div class='topbar-title'>Research Assistant Studio</div>"
        "<div class='topbar-sub'>"
        "Left pane: chat + report output. Right pane: real-time agent dashboard and event stream."
        "</div>"
        "</div>"
    ),
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([1.3, 1], gap="large")

with left_col:
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    st.markdown("<div class='panel-title'>Query Input</div>", unsafe_allow_html=True)
    query = st.text_area(
        "Research Query",
        placeholder="Ask a research question...",
        height=92,
        label_visibility="collapsed",
        key="query_input",
    )
    run_button = st.button("Run Research", type="primary", use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    chat_box = st.container()
    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    render_chat(st.session_state.chat_messages, chat_box)
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='panel'>", unsafe_allow_html=True)
    tabs = st.tabs(["Report Viewer", "Agent Outputs"]) 

    with tabs[0]:
        if st.session_state.last_result:
            st.markdown(st.session_state.last_result["report"])
            st.download_button(
                "Download Report",
                data=st.session_state.last_result["report"],
                file_name=safe_report_filename(st.session_state.last_result["query"]),
                mime="text/markdown",
            )
        else:
            st.caption("Run research to see the generated report here.")

    with tabs[1]:
        if st.session_state.last_result:
            for agent_result in st.session_state.last_result["agent_results"]:
                with st.expander(agent_result.get("agent", "Agent"), expanded=False):
                    st.markdown(agent_result.get("findings", "No findings"))
                    papers = agent_result.get("papers") or []
                    if papers:
                        st.markdown("**Top papers**")
                        for paper in papers:
                            title = paper.get("title", "Untitled")
                            url = paper.get("url", "")
                            st.markdown(f"- [{title}]({url})")
        else:
            st.caption("Agent outputs will appear after execution.")

    st.markdown("</div>", unsafe_allow_html=True)

with right_col:
    dashboard_placeholder = st.empty()

if run_button:
    if not query.strip():
        st.warning("Please enter a research query.")
        render_dashboard(st.session_state.live_state, dashboard_placeholder, st.session_state.run_history)
        st.stop()

    if not os.getenv("OPENAI_API_KEY"):
        st.error("OPENAI_API_KEY is missing. Add it to `.env` or system environment and restart.")
        render_dashboard(st.session_state.live_state, dashboard_placeholder, st.session_state.run_history)
        st.stop()

    st.session_state.chat_messages.append({"role": "user", "content": query.strip()})

    image_urls = [line.strip() for line in image_urls_input.splitlines() if line.strip()]
    image_paths = save_uploaded_images(uploaded_images)

    from src.orchestrator import ResearchOrchestrator

    st.session_state.orchestrator = ResearchOrchestrator()
    live_state = init_live_state()
    live_state["run_start"] = time.time()
    st.session_state.live_state = live_state

    def progress_callback(event_or_stage, message: str = ""):
        payload = event_or_stage if isinstance(event_or_stage, dict) else {"stage": event_or_stage, "message": message}
        add_event(st.session_state.live_state, payload)
        render_dashboard(st.session_state.live_state, dashboard_placeholder, st.session_state.run_history)

    render_dashboard(st.session_state.live_state, dashboard_placeholder, st.session_state.run_history)

    try:
        result = st.session_state.orchestrator.run(
            query=query.strip(),
            image_urls=image_urls,
            image_paths=image_paths,
            progress_callback=progress_callback,
        )
    except Exception as exc:
        cleanup_paths(image_paths)
        record_run(query=query, live_state=st.session_state.live_state, result=None, error=str(exc))
        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": f"Run failed: {exc}",
            }
        )
        st.error(f"Research failed: {exc}")
        render_dashboard(st.session_state.live_state, dashboard_placeholder, st.session_state.run_history)
        st.stop()

    cleanup_paths(image_paths)

    if "error" in result:
        record_run(query=query, live_state=st.session_state.live_state, result=None, error=result["error"])
        st.session_state.chat_messages.append(
            {
                "role": "assistant",
                "content": result["error"],
            }
        )
        st.error(result["error"])
        render_dashboard(st.session_state.live_state, dashboard_placeholder, st.session_state.run_history)
        st.stop()

    st.session_state.last_result = result
    record_run(query=query, live_state=st.session_state.live_state, result=result)

    summary_text = result["report"][:700]
    if len(result["report"]) > 700:
        summary_text += "..."
    st.session_state.chat_messages.append(
        {
            "role": "assistant",
            "content": (
                f"Research complete with {result['agent_count']} agent(s).\n\n"
                f"{summary_text}"
            ),
        }
    )

    render_dashboard(st.session_state.live_state, dashboard_placeholder, st.session_state.run_history)
    st.rerun()

render_dashboard(st.session_state.live_state, dashboard_placeholder, st.session_state.run_history)
st.markdown("<div class='small-muted'>Tip: keep this dashboard pane open while submitting multiple queries to compare runs.</div>", unsafe_allow_html=True)
