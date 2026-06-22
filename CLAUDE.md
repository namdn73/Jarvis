# Jarvis — Personal Voice AI Assistant

## Project Overview

Jarvis is a wake-word-activated personal voice assistant that listens for "Jarvis",
greets the user, accepts a spoken query, searches the web or answers from knowledge,
speaks a summary back, and displays results as cards in a React UI.

## Tech Stack

| Concern | Library / Tool |
|---|---|
| Wake word | `openwakeword` — "hey Jarvis" keyword, free, no API key |
| STT | `openai-whisper` — `base` model, CPU only (no GPU on dev machine) |
| TTS | `edge-tts` — voice: `en-GB-RyanNeural` |
| Agent | `deepagents` (LangChain DeepAgent on LangGraph) |
| LLM | `gemini-2.0-flash` via `langchain-google-genai` |
| Search | `tavily-python` — agent picks news vs. general vs. no search |
| Backend | `FastAPI` (async throughout) |
| Frontend | React + Vite + TypeScript |
| DB | SQLite via SQLAlchemy — 3 tables: `sessions`, `queries`, `results` |
| Package mgr | `uv` (Python), `npm` (frontend) |
| Deployment | Native Windows — no Docker |

## Implementation Plans

Before implementing any module, read the relevant plan file first:

- **System architecture, state machine, data flow** → [ImplementationPlan/general/architecture.md](ImplementationPlan/general/architecture.md)
- **Backend implementation** → [ImplementationPlan/backend/plan.md](ImplementationPlan/backend/plan.md)
- **Frontend implementation** → [ImplementationPlan/frontend/plan.md](ImplementationPlan/frontend/plan.md)

> Project folder structure will be added here after the structure discussion.

## Voice Interaction Flow

```
STANDBY
  └─ wake word detected
       └─ GREETING  → TTS: "Hello sir, how can I help you today?"
            └─ LISTENING  (10s timeout → "Goodbye sir" → STANDBY)
                 └─ PROCESSING  → DeepAgent runs
                      └─ RESPONDING  → TTS summary + WebSocket pushes cards
                           └─ ACTIVE_WINDOW  (30s follow-up window)
                                ├─ follow-up query → back to LISTENING
                                └─ silence 30s → STANDBY
```

## Agent Tools

| Tool | Trigger | Implementation |
|---|---|---|
| `tavily_search(query, mode)` | Any info/news query | Tavily API, agent picks `"news"` or `"general"` |
| `open_result(ref)` | "open one", "open the Reuters one" | regex for index, `difflib` for natural ref, `webbrowser.open()` |
| `tell_time_date()` | "what time is it" | `datetime.now()` — no API needed |

## Memory Model

- **Preferences** — topics the user follows, persisted in SQLite indefinitely
- **Session recall** — last session reloaded if within 2 hours; clean slate otherwise
- **History** — all sessions/queries/results stored in SQLite for user browsing

## UI Design

- Dark theme, cyan/blue accents — Iron Man JARVIS aesthetic
- Split view: left panel (conversation log + waveform visualiser), right panel (result cards)
- 5 cards max per search query; single text card for knowledge answers (no URL)
- Results replace on each new query
- Waveform visualiser active during LISTENING and RESPONDING states

## Coding Standards

- **KISS** — Keep It Simple. Prefer the straightforward solution over the clever one.
- **DRY** — Don't repeat logic. Extract shared behaviour into a single reusable function.
- All Python functions must have type hints
- Prefer `async`/`await` for all I/O-bound code (FastAPI handlers, agent calls, TTS, search)
- Git commits follow Conventional Commits: `feat:`, `fix:`, `chore:`, `docs:`, `refactor:`
- Every public function gets a one-line docstring

## Rules for Claude

### Never Do
- Use `pip` or `conda` directly — always use `uv`
- Add Docker configuration (mic access does not work on Windows Docker)
- Assume GPU availability — Whisper runs on CPU only
- Use `ffmpeg` for audio — decode WAV with stdlib `wave` + numpy
- Store real secrets in any committed file
- Implement a module before reading its `ImplementationPlan/` file
- Add abstractions, helpers, or error handling for scenarios that cannot happen

### Always Do
- Use `async def` for all FastAPI route handlers and agent calls
- Load config from `.env` via `python-dotenv` — never hardcode API keys
- Wrap all LLM/API calls in `try/except` with safe defaults and stderr logging
- Keep agent tools stateless — tools read state, never mutate it directly
- Read the relevant `ImplementationPlan/` file before implementing any new module
- Apply KISS and DRY on every function written

### Uncertainty Handling
Make a reasonable choice, implement it, and leave a one-line comment explaining the decision.
Ask only when the choice would be irreversible or security-sensitive.

## Common Commands

```bash
# Backend
uv sync                                   # install / sync Python deps
uv run uvicorn backend.main:app --reload  # start FastAPI dev server

# Frontend
cd frontend && npm install                # install JS deps
cd frontend && npm run dev                # start Vite dev server

# Tests
uv run pytest                             # run all backend tests
cd frontend && npm run test               # run vitest

# Add a Python package
uv add <package>

# Add a frontend package
cd frontend && npm install <package>
```

## API Keys Required

| Key | Purpose | Where to get |
|---|---|---|
| `GEMINI_API_KEY` | gemini-2.0-flash LLM | aistudio.google.com — free tier |
| `TAVILY_API_KEY` | Web search | tavily.com — free tier |

## MCP Servers

| Server | Transport | Purpose |
|---|---|---|
| `docs-langchain` | HTTP → `https://docs.langchain.com/mcp` | Query LangChain / LangGraph / DeepAgent docs directly |

### Available tools
- `mcp__docs-langchain__search_docs_by_lang_chain` — keyword search across LangChain docs
- `mcp__docs-langchain__query_docs_filesystem_docs_by_lang_chain` — browse docs by path

### When to use
Always use these tools instead of WebSearch when looking up anything LangChain-related:
`deepagents`, `create_deep_agent`, LangGraph APIs, `langchain-google-genai`, tool definitions,
agent invocation patterns, middleware, HarnessProfile, etc.

### How to add (if reconfiguring)
```bash
claude mcp add --transport http docs-langchain https://docs.langchain.com/mcp
```
