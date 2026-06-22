# Jarvis — Personal Voice AI Assistant

> *"Hello sir, how can I help you today?"*

Jarvis is a wake-word-activated personal AI assistant inspired by Iron Man's J.A.R.V.I.S. Say **"hey Jarvis"** and it wakes up, listens to your question, searches the web or answers from its own knowledge, speaks a summary back to you, and displays results as cards in a sleek holographic-style interface.

---

## What Jarvis can do

- **Wake word activation** — Say "hey Jarvis" and it's ready. No button, no click.
- **Voice queries** — Ask anything in natural speech. Jarvis transcribes it locally using Whisper.
- **Web search** — Jarvis decides whether to search the web (news or general) or answer from its own knowledge. Powered by Tavily and Gemini.
- **Spoken responses** — Jarvis speaks its answer back to you in a natural British voice before displaying the results.
- **Result cards** — Up to 5 article cards appear on screen with headline, source, and snippet.
- **Open links by voice** — Say "open the first one" or "open the Reuters article" and Jarvis opens it in your browser.
- **Follow-up queries** — After answering, Jarvis stays active for 30 seconds to handle follow-up questions without needing to say "hey Jarvis" again.
- **Remembers your preferences** — Tell Jarvis what topics you follow and it remembers across sessions.

---

## Tech stack

| Concern | Tool |
|---|---|
| Wake word | `openwakeword` — "hey Jarvis", runs locally, free |
| Speech-to-text | `openai-whisper` base model, CPU only |
| Text-to-speech | `edge-tts` — British male voice (`en-GB-RyanNeural`) |
| AI agent | LangChain DeepAgent on LangGraph |
| LLM | Google Gemini 2.0 Flash (free tier) |
| Web search | Tavily API (free tier) |
| Backend | FastAPI + Python |
| Frontend | React + Vite + TypeScript |
| Database | SQLite — conversation history |

---

## Requirements

- Windows (mic access requirement — no Docker)
- Python 3.11+
- Node.js 18+
- `uv` package manager

API keys needed (both free tier):
- `GEMINI_API_KEY` — [aistudio.google.com](https://aistudio.google.com)
- `TAVILY_API_KEY` — [tavily.com](https://tavily.com)

---

## Getting started

```bash
# Install Python dependencies
uv sync

# Install frontend dependencies
cd frontend && npm install

# Copy and fill in your API keys
cp .env.example .env

# Start the backend
uv run uvicorn backend.main:app --reload

# Start the frontend (separate terminal)
cd frontend && npm run dev
```

Then open `http://localhost:5173` and say **"hey Jarvis"**.

---

## Project status

Work in progress — see [ImplementationPlan/general/task.md](ImplementationPlan/general/task.md) for current progress.
