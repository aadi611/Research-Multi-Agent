# Multi-Agent Research Assistant

An AI-powered research system using Claude claude-opus-4-6 with multiple specialized agents, memory layers, and contradiction detection.

## Architecture

```
Task Query → Streamlit UI → Orchestrator
                                ├── Memory Cache (Redis + ChromaDB)
                                ├── Web Research Agent     → Claude + web_search
                                ├── ArXiv Research Agent   → Claude + arxiv tool
                                ├── Multi-Modal Agent      → Claude vision
                                ├── Research Validator     → contradiction detection
                                └── Report Generator       → final synthesis
```

## Setup

1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your ANTHROPIC_API_KEY
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
