"""Multi-Agent Research Assistant — Streamlit UI"""
import os
import time
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

st.set_page_config(
    page_title="Multi-Agent Research Assistant",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styles ──────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
.agent-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 16px;
    margin: 8px 0;
    background: #f8f9fa;
}
.agent-header {
    font-weight: bold;
    font-size: 1.1em;
    margin-bottom: 8px;
}
.contradiction-box {
    border-left: 4px solid #ff6b6b;
    padding: 12px;
    background: #fff5f5;
    border-radius: 4px;
    margin: 8px 0;
}
.resolved-box {
    border-left: 4px solid #51cf66;
    padding: 12px;
    background: #f4fef4;
    border-radius: 4px;
    margin: 8px 0;
}
</style>
""",
    unsafe_allow_html=True,
)

# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.title("🔬 Research Assistant")
    st.markdown("**Multi-Agent AI Research System**")
    st.divider()

    st.subheader("Architecture")
    st.markdown("""
- 🌐 **Web Research Agent** — current info via web search
- 📚 **ArXiv Agent** — academic papers
- 🖼️ **Multi-Modal Agent** — visual content
- 🧠 **Memory Layer** — Redis + ChromaDB
- ✅ **Research Validator** — contradiction detection
- 📝 **Report Generator** — final synthesis
""")

    st.divider()
    st.subheader("Settings")

    api_key = st.text_input(
        "OpenAI API Key",
        value=os.getenv("OPENAI_API_KEY", ""),
        type="password",
        help="Enter your OpenAI API key",
    )
    if api_key:
        os.environ["OPENAI_API_KEY"] = api_key

    st.divider()
    st.subheader("Image Analysis (Optional)")
    image_urls_input = st.text_area(
        "Image URLs (one per line)",
        placeholder="https://example.com/chart.png",
        height=80,
    )
    uploaded_images = st.file_uploader(
        "Upload Images",
        accept_multiple_files=True,
        type=["jpg", "jpeg", "png", "webp"],
    )

    st.divider()
    if st.button("🗑️ Clear Cache", use_container_width=True):
        if "orchestrator" in st.session_state:
            st.session_state.orchestrator.cache.clear()
            st.success("Cache cleared!")

# ── Main Content ─────────────────────────────────────────────────────────────
st.title("🔬 Multi-Agent Research Assistant")
st.markdown("Ask any research question and multiple AI agents will investigate from different angles.")

query = st.text_area(
    "Research Query",
    placeholder="e.g. What are the latest advances in quantum computing error correction?",
    height=100,
    label_visibility="collapsed",
)

col1, col2 = st.columns([1, 5])
with col1:
    run_button = st.button("🚀 Research", type="primary", use_container_width=True)

# ── Run Research ──────────────────────────────────────────────────────────────
if run_button:
    if not query.strip():
        st.warning("Please enter a research query.")
        st.stop()

    if not os.getenv("OPENAI_API_KEY"):
        st.error("Please enter your OpenAI API key in the sidebar.")
        st.stop()

    # Parse image inputs
    image_urls = [u.strip() for u in image_urls_input.strip().splitlines() if u.strip()]
    image_paths = []

    # Save uploaded files temporarily
    if uploaded_images:
        import tempfile
        for uploaded in uploaded_images:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=f"_{uploaded.name}"
            ) as f:
                f.write(uploaded.read())
                image_paths.append(f.name)

    # Init orchestrator (cached in session)
    if "orchestrator" not in st.session_state:
        with st.spinner("Initializing research system..."):
            from src.orchestrator import ResearchOrchestrator
            st.session_state.orchestrator = ResearchOrchestrator()

    orchestrator = st.session_state.orchestrator

    # Progress tracking
    progress_log = []
    status_container = st.empty()
    agent_status = {
        "cache": "⏳", "memory": "⏳", "plan": "⏳",
        "web": "⏳", "arxiv": "⏳", "multimodal": "⏳",
        "validate": "⏳", "report": "⏳",
    }

    def progress_callback(stage: str, message: str):
        progress_log.append((stage, message))
        if stage in agent_status:
            if "✅" in message:
                agent_status[stage] = "✅"
            elif "⚠️" in message:
                agent_status[stage] = "⚠️"
            else:
                agent_status[stage] = "🔄"

        with status_container.container():
            st.markdown("**Research Progress**")
            cols = st.columns(4)
            stage_labels = [
                ("cache", "Cache"),
                ("plan", "Planning"),
                ("web", "Web Agent"),
                ("arxiv", "ArXiv Agent"),
                ("multimodal", "Multi-Modal"),
                ("validate", "Validator"),
                ("report", "Report"),
            ]
            for i, (s, label) in enumerate(stage_labels):
                cols[i % 4].markdown(f"{agent_status[s]} {label}")

            if progress_log:
                st.caption(f"→ {progress_log[-1][1]}")

    start_time = time.time()

    with st.spinner("Running multi-agent research..."):
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

    elapsed = time.time() - start_time
    status_container.empty()

    if "error" in result:
        st.error(result["error"])
        st.stop()

    # ── Results ──────────────────────────────────────────────────────────────
    st.success(f"Research complete in {elapsed:.1f}s · {result['agent_count']} agents")

    # Final Report
    st.markdown("---")
    st.header("📄 Research Report")
    st.markdown(result["report"])

    # Agent Details (expandable)
    st.markdown("---")
    st.header("🤖 Agent Findings")
    agent_tabs = st.tabs([r["agent"] for r in result["agent_results"]])
    for tab, agent_result in zip(agent_tabs, result["agent_results"]):
        with tab:
            st.markdown(agent_result.get("findings", "No findings"))
            if "papers" in agent_result and agent_result["papers"]:
                st.subheader("📄 Papers Found")
                for paper in agent_result["papers"]:
                    st.markdown(
                        f"- [{paper['title']}]({paper['url']}) — {', '.join(paper['authors'])} ({paper['published']})"
                    )

    # Validation Results
    st.markdown("---")
    st.header("✅ Validation")
    validation = result["validation"]
    confidence_color = {"high": "🟢", "medium": "🟡", "low": "🔴"}.get(
        validation.get("confidence", "low"), "⚪"
    )
    st.markdown(f"**Confidence:** {confidence_color} {validation.get('confidence', 'unknown').title()}")

    if validation.get("consistent_findings"):
        st.subheader("Points of Consensus")
        for finding in validation["consistent_findings"]:
            st.markdown(f"✓ {finding}")

    if validation.get("has_contradictions") and validation.get("contradictions"):
        st.subheader("Contradictions Detected & Resolved")
        for i, (contradiction, resolution) in enumerate(
            zip(validation["contradictions"], result.get("resolutions", []))
        ):
            with st.expander(f"Contradiction {i+1}: {contradiction.get('topic', 'Unknown')}"):
                st.markdown(
                    f'<div class="contradiction-box">⚠️ <b>{contradiction.get("claim_a")}</b><br>vs.<br>⚠️ <b>{contradiction.get("claim_b")}</b></div>',
                    unsafe_allow_html=True,
                )
                if resolution:
                    st.markdown(
                        f'<div class="resolved-box">✅ <b>Resolution:</b><br>{resolution.get("resolution", "")}</div>',
                        unsafe_allow_html=True,
                    )

    # Research Plan
    with st.expander("🗺️ Research Plan"):
        plan = result.get("plan", {})
        col1, col2, col3 = st.columns(3)
        col1.metric("Web Agent", "Active" if plan.get("use_web") else "Skipped")
        col2.metric("ArXiv Agent", "Active" if plan.get("use_arxiv") else "Skipped")
        col3.metric("Multi-Modal", "Active" if plan.get("use_multimodal") else "Skipped")
        st.caption(f"Rationale: {plan.get('rationale', 'N/A')}")

    # Download report
    st.download_button(
        "⬇️ Download Report",
        data=result["report"],
        file_name=f"research_{query[:30].replace(' ', '_')}.md",
        mime="text/markdown",
    )

# ── Empty state ───────────────────────────────────────────────────────────────
else:
    st.markdown("""
### How it works

1. **Enter your research query** — any topic, question, or problem
2. **Agents run in parallel:**
   - 🌐 *Web Agent* searches the internet for current information
   - 📚 *ArXiv Agent* finds relevant academic papers
   - 🖼️ *Multi-Modal Agent* analyzes any images you provide
3. **Research Validator** checks for contradictions between sources and resolves them
4. **Report Generator** synthesizes everything into a comprehensive report

---
**Example queries:**
- *What are the latest breakthroughs in mRNA vaccine technology?*
- *How does transformer attention mechanism work?*
- *What is the current state of fusion energy research?*
- *Compare CRISPR-Cas9 vs base editing techniques*
""")
