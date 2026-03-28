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

## Live Workflow UI

The Streamlit app now includes a control-room view that shows:

- Ordered timeline of workflow events with timestamps
- Live stage status (`running`, `completed`, `failed`)
- Current active stage and per-stage duration
- Agent findings, contradictions, resolutions, and final report

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
| `OPENAI_API_KEY` | Yes | Your OpenAI API key |
| `REDIS_URL` | No | Redis connection URL (default: in-memory cache) |
| `CHROMA_DB_PATH` | No | ChromaDB storage path (default: `./chroma_db`) |

# Research-Multi-Agent
