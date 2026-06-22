# Jarvis — Implementation Task List

Reference plans:
- Architecture  → [ImplementationPlan/general/architecture.md](architecture.md)
- Backend       → [ImplementationPlan/backend/plan.md](../backend/plan.md)
- Frontend      → [ImplementationPlan/frontend/plan.md](../frontend/plan.md)

---

## Session 1 — Project Scaffold ✓

- [x] Create full folder structure (backend/, frontend/, all `__init__.py` files)
- [x] Create `backend/prompts/` with `system.md`, `greeting.txt`, `goodbye.txt` (content from backend plan)
- [x] Create `backend/agent_data/memories/` directory (`AGENTS.md` auto-created by agent on first run)
- [x] Initialise git repository + initial commit
- [x] Verify `pyproject.toml` is correct and `uv sync` installs cleanly
- [x] Verify `.env` has all 2 API keys filled in (Gemini + Tavily)

---

## Session 2 — Backend Core (config, state, DB)

- [ ] `backend/config.py` — typed constants grouped by concern (API, Server, Audio, Paths) + `load_prompt()` helper
- [ ] `backend/state.py` — JarvisStatus enum, JarvisState dataclass, asyncio.Queue
- [ ] `backend/db/models.py` — 3 SQLAlchemy ORM models (sessions, queries, results) — preferences handled by AGENTS.md
- [ ] `backend/db/database.py` — sync engine, SessionLocal, get_db()
- [ ] `backend/main.py` — FastAPI app skeleton + lifespan (DB init only, no audio yet)
- [ ] Smoke test: `uv run uvicorn backend.main:app --reload` starts with no errors

---

## Session 3 — Backend Audio Pipeline

- [ ] `backend/audio/speaker.py` — edge-tts → WAV temp file → sounddevice playback
- [ ] `backend/audio/wake_word.py` — openWakeWord + sounddevice blocking loop ("hey Jarvis")
- [ ] `backend/audio/listener.py` — VAD (RMS), Whisper transcription, amplitude streaming
- [ ] Wire audio thread into `main.py` lifespan startup
- [ ] Manual test: say "hey Jarvis" → greeting plays through speakers

---

## Session 4 — Backend Agent & Tools

- [ ] `backend/agent/tools/search.py` — tavily_search() callable
- [ ] `backend/agent/tools/datetime_tool.py` — tell_time_date() callable
- [ ] `backend/agent/tools/browser.py` — open_result() with regex + difflib
- [ ] `backend/agent/jarvis_agent.py` — DeepAgent with FilesystemBackend + MemorySaver + memory=[AGENTS.md], system prompt loaded from file, thread_id for ACTIVE_WINDOW continuity
- [ ] Manual test: run agent.run("what time is it?") in isolation → returns valid dict

---

## Session 5 — Backend API & WebSocket

- [ ] `backend/api/websocket.py` — WS endpoint, queue consumer loop, broadcast
- [ ] `backend/api/routes.py` — /health, /history, /preferences endpoints
- [ ] Wire WebSocket + routes into `main.py`
- [ ] Wire full pipeline: wake word → agent → WS broadcast
- [ ] Manual test: open DevTools → WS tab → say "Jarvis" → verify all 5 message types appear

---

## Session 6 — Backend Tests

- [ ] `tests/test_state.py` — JarvisStatus transitions
- [ ] `tests/test_tools.py` — tavily_search, tell_time_date, open_result (mocked)
- [ ] `tests/test_agent.py` — agent.run() with mocked ainvoke
- [ ] `tests/test_websocket.py` — queue → WS broadcast
- [ ] `tests/test_routes.py` — /health, /history, /preferences
- [ ] `uv run pytest` — all tests pass

---

## Session 7 — Frontend Setup & Foundation

- [ ] Scaffold Vite + React + TypeScript project in `frontend/`
- [ ] Install and configure Tailwind CSS v4 + JARVIS colour palette + Orbitron font
- [ ] `frontend/src/types.ts` — JarvisStatus, ResultItem, WsMessage, JarvisState types
- [ ] `frontend/src/context/JarvisContext.tsx` — useReducer + Context + useJarvis hook
- [ ] `frontend/src/hooks/useWebSocket.ts` — native WS, reconnect, dispatch to reducer
- [ ] `frontend/src/hooks/useMouseActivity.ts` — mousemove debounce hook
- [ ] Configure Vite proxy for `/ws` → `http://localhost:8000`
- [ ] Smoke test: `npm run dev` starts, no TS errors

---

## Session 8 — Frontend Canvas Components

- [ ] `frontend/src/components/SphereCanvas.tsx` — Fibonacci sphere, rotation, glow, pulse
- [ ] `frontend/src/components/WaveformCanvas.tsx` — rolling amplitude buffer, bar chart
- [ ] Visual test: sphere rotates on black background, waveform animates with mock data

---

## Session 9 — Frontend UI Components

- [ ] `frontend/src/components/StatusBadge.tsx` — colour map for all 6 states
- [ ] `frontend/src/components/ResultCard.tsx` — dark panel, hover glow, open link
- [ ] `frontend/src/components/ConversationLog.tsx` — chat entries, auto-scroll
- [ ] `frontend/src/components/LeftPanel.tsx` — orb + badge + waveform + log
- [ ] `frontend/src/components/RightPanel.tsx` — card list, fade-in stagger, skeleton
- [ ] `frontend/src/App.tsx` — IDLE/ACTIVE layout switch, mouse wake, WS integration

---

## Session 10 — Frontend Tests

- [ ] `frontend/src/tests/reducer.test.ts` — all 5 WS message type transitions
- [ ] `frontend/src/tests/useWebSocket.test.ts` — connect, dispatch, reconnect logic
- [ ] `npm run test` — all tests pass

---

## Session 11 — Integration & Polish

- [ ] Full end-to-end test: wake word → greeting → query → results → cards displayed
- [ ] Test session recall: results reload within 2-hour window
- [ ] Test follow-up: "open the first one" → browser opens URL
- [ ] Test STANDBY return: sphere fades back in after 30s silence
- [ ] Build frontend: `npm run build` → `frontend/dist/` created
- [ ] Serve via FastAPI: `uv run uvicorn backend.main:app` → visit `localhost:8000`
- [ ] Update `CLAUDE.md` with final project folder structure
