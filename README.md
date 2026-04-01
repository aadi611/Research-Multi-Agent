# Multi-Agent Research Assistant

An AI-powered research system built on OpenAI models with specialized agents, memory layers, contradiction detection, and a real-time workflow UI.

## Architecture

```
Task Query → Streamlit UI → Orchestrator
                                ├── Memory Cache (Redis + ChromaDB)
                                ├── Web Research Agent     → OpenAI + web_search
                                ├── ArXiv Research Agent   → OpenAI + arxiv tool
                                ├── Multi-Modal Agent      → OpenAI vision
                                ├── Research Validator     → contradiction detection
                                └── Report Generator       → final synthesis
```

## Production UI

The Streamlit frontend now uses a split-pane production layout:

- **Left pane**: query input, chat-style history, and in-page report viewer
- **Right pane**: live operations dashboard with stage KPIs and event stream
- **Workflow canvas**: node-based Webhook -> Agent -> Router -> Response view
- **Live updates**: stage state and event timeline update in real time during run

You can read the generated report directly in the web UI and download it as markdown.

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

3. **Run**
   ```bash
   streamlit run main.py
   ```

## Optional Services

- **Redis** — for persistent caching across sessions (falls back to in-memory)
- **ChromaDB** — for semantic search of past research (auto-configured locally)

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `OPENAI_API_KEY` | Yes | Add your OpenAI API key |
| `REDIS_URL` | No | Redis connection URL (default: in-memory cache) |
| `CHROMA_DB_PATH` | No | ChromaDB storage path (default: `./chroma_db`) |

# Research-Multi-Agent
