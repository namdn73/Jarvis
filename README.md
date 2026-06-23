# J.A.R.V.I.S — Personal Voice AI Assistant

> *"Hello sir, how can I help you today?"*

Your own Iron Man AI. Wake it with your voice, ask anything, and watch the answers materialize on a holographic dark interface — while Jarvis speaks them back to you in real time. Fully local, always listening, zero cloud dependency for audio.

---

![Jarvis UI](assets/screenshot.png)

---

## Features

- **Wake word** — Say "hey Jarvis" to activate. No button, no click, always listening.
- **Voice queries** — Speak naturally. Whisper transcribes locally on CPU, no cloud STT.
- **Smart search** — The agent decides: search news, search the web, or answer from its own knowledge.
- **Spoken responses** — Jarvis speaks its answer in a British voice, sentence by sentence as it generates.
- **Result cards** — Up to 5 article cards with headline, source, and snippet appear on screen.
- **Open by voice** — "Open the first one" or "Open the Reuters article" launches it in your browser.
- **Follow-up conversations** — Jarvis stays active for 30 seconds after answering. Ask follow-ups without re-triggering the wake word. Full conversation memory within the session.
- **Remembers you** — Tell Jarvis your interests and it remembers across sessions via a local memory file.

---

## UI Preview

> Replace `assets/screenshot.png` with your own screenshot after first run.

The interface has two modes:

**IDLE** — Fullscreen rotating cyan Fibonacci sphere on black. Waiting for "hey Jarvis".

**ACTIVE** — Split view: sphere shrinks to top-left orb, left panel shows conversation log and waveform visualiser, right panel shows result cards with fade-in animation.

---

## Tech stack

| Concern | Tool |
|---|---|
| Wake word | `openwakeword` — "hey Jarvis", runs locally, free, no API key |
| Speech-to-text | `openai-whisper` tiny model, CPU |
| Text-to-speech | `edge-tts` — British male voice (`en-GB-RyanNeural`) |
| AI agent | LangChain DeepAgent (LangGraph) |
| LLM | Google Gemini Flash (free tier, 1500 req/day) |
| Web search | Tavily API (free tier, 1000 req/month) |
| Backend | FastAPI + Python 3.11 |
| Frontend | React + Vite + TypeScript + Tailwind CSS |
| Database | SQLite — conversation history |
| Font | Orbitron — Iron Man HUD aesthetic |

---

## Requirements

- **Windows** — mic access works natively (no Docker)
- **Python 3.11+** and **Node.js 18+**
- **`uv`** package manager — [install](https://docs.astral.sh/uv/getting-started/installation/)

API keys (both free tier, no credit card):

| Key | Get it at |
|---|---|
| `GEMINI_API_KEY` | [aistudio.google.com](https://aistudio.google.com) |
| `TAVILY_API_KEY` | [tavily.com](https://tavily.com) |

---

## Getting started

```bash
# 1. Install Python dependencies
uv sync

# 2. Install frontend dependencies
cd frontend && npm install && cd ..

# 3. Set up your API keys
cp .env.example .env
# Edit .env and fill in GEMINI_API_KEY and TAVILY_API_KEY

# 4. Build the frontend
cd frontend && npm run build && cd ..

# 5. Start Jarvis
uv run uvicorn backend.main:app
```

Open `http://localhost:8000` and say **"hey Jarvis"**.

### Development mode (hot reload)

```bash
# Terminal 1 — backend
uv run uvicorn backend.main:app --reload

# Terminal 2 — frontend dev server
cd frontend && npm run dev
```

Then open `http://localhost:5173`.

---

## How it works

```
"hey Jarvis"
     │
     ▼
  Greeting  →  "Hello sir, how can I help you today?"
     │
     ▼
  Listening  →  Whisper transcribes your query
     │
     ▼
  Processing  →  Gemini agent picks: search news / search web / answer directly
     │
     ▼
  Responding  →  Speaks answer + displays result cards
     │
     ▼
  Active window (30s)  →  follow-up questions without re-triggering
     │
     ▼
  Standby  →  waiting for "hey Jarvis" again
```

---

## Project structure

```
project/
├── backend/             ← FastAPI + audio pipeline + agent
├── frontend/            ← React UI
├── tests/               ← pytest suite (42 tests)
├── ImplementationPlan/  ← architecture + task tracking
└── .env                 ← your API keys (never committed)
```

See [ImplementationPlan/general/task.md](ImplementationPlan/general/task.md) for the full build roadmap.
