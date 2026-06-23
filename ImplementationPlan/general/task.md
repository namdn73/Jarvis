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

## Session 2 — Backend Core (config, state, DB) ✓

- [x] `backend/config.py` — typed constants grouped by concern (API, Server, Audio, Paths) + `load_prompt()` helper
- [x] `backend/state.py` — JarvisStatus enum, JarvisState dataclass, asyncio.Queue
- [x] `backend/db/models.py` — 3 SQLAlchemy ORM models (sessions, queries, results) — preferences handled by AGENTS.md
- [x] `backend/db/database.py` — sync engine, SessionLocal, get_db()
- [x] `backend/main.py` — FastAPI app skeleton + lifespan (DB init only, no audio yet)
- [x] Smoke test: `uv run uvicorn backend.main:app --reload` starts with no errors

---

## Session 3 — Backend Audio Pipeline

- [x] `backend/audio/speaker.py` — edge-tts → WAV temp file → sounddevice playback
- [x] `backend/audio/wake_word.py` — openWakeWord + sounddevice blocking loop ("hey Jarvis")
- [x] `backend/audio/listener.py` — VAD (RMS), Whisper transcription, amplitude streaming
- [x] Wire audio thread into `main.py` lifespan startup
- [x] Manual test: say "hey Jarvis" → greeting plays through speakers

---

## Session 4 — Backend Agent & Tools ✓

- [x] `backend/agent/tools/search.py` — tavily_search() callable
- [x] `backend/agent/tools/datetime_tool.py` — tell_time_date() callable
- [x] `backend/agent/tools/browser.py` — open_result() with regex + difflib
- [x] `backend/agent/jarvis_agent.py` — DeepAgent with FilesystemBackend + MemorySaver + memory=[AGENTS.md], system prompt loaded from file, thread_id for ACTIVE_WINDOW continuity
- [x] Manual test: run agent.run("what time is it?") in isolation → returns valid dict

---

## Session 5 — Backend API & WebSocket ✓

- [x] `backend/api/websocket.py` — WS endpoint, queue consumer loop, broadcast
- [x] `backend/api/routes.py` — /health, /history, /preferences endpoints
- [x] Wire WebSocket + routes into `main.py`
- [x] Wire full pipeline: wake word → agent → WS broadcast
- [x] Manual test: open DevTools → WS tab → say "Jarvis" → verify all 5 message types appear

---

## Session 5B — Backend Latency Optimizations

- [x] `.env`: set `WHISPER_MODEL=tiny` and `SILENCE_FRAMES=12`
- [x] `backend/agent/jarvis_agent.py`: add `register_harness_profile` block to exclude built-in DeepAgent tools and disable subagent
- [x] `backend/audio/speaker.py`: split `speak()` into sentence loop + `_speak_one()` for streaming TTS
- [ ] Manual test: say "hey Jarvis, what time is it?" — full round-trip under 3s
- [ ] Manual test: say "hey Jarvis, what's the latest AI news?" — first TTS sentence plays while cards load

---

## Session 6 — Backend Tests ✓

- [x] `tests/test_state.py` — JarvisStatus transitions
- [x] `tests/test_tools.py` — tavily_search, tell_time_date, open_result (mocked)
- [x] `tests/test_agent.py` — agent.run() with mocked ainvoke
- [x] `tests/test_websocket.py` — queue → WS broadcast
- [x] `tests/test_routes.py` — /health, /history, /preferences
- [x] `uv run pytest` — all tests pass

---

## Session 7 — Frontend Setup & Foundation ✓

- [x] Scaffold Vite + React + TypeScript project in `frontend/`
- [x] Install and configure Tailwind CSS v4 + JARVIS colour palette + Orbitron font
- [x] `frontend/src/types.ts` — JarvisStatus, ResultItem, WsMessage, JarvisState types
- [x] `frontend/src/context/JarvisContext.tsx` — useReducer + Context + useJarvis hook
- [x] `frontend/src/hooks/useWebSocket.ts` — native WS, reconnect, dispatch to reducer
- [x] `frontend/src/hooks/useMouseActivity.ts` — mousemove debounce hook
- [x] Configure Vite proxy for `/ws` → `http://localhost:8000`
- [x] Smoke test: `npm run dev` starts, no TS errors

---

## Session 8 — Frontend Canvas Components ✓

- [x] `frontend/src/components/SphereCanvas.tsx` — Fibonacci sphere, rotation, glow, pulse
- [x] `frontend/src/components/WaveformCanvas.tsx` — rolling amplitude buffer, bar chart
- [x] Visual test: sphere rotates on black background, waveform animates with mock data

---

## Session 9 — Frontend UI Components ✓

- [x] `frontend/src/components/StatusBadge.tsx` — colour map for all 6 states
- [x] `frontend/src/components/ResultCard.tsx` — dark panel, hover glow, open link
- [x] `frontend/src/components/ConversationLog.tsx` — chat entries, auto-scroll
- [x] `frontend/src/components/LeftPanel.tsx` — orb + badge + waveform + log
- [x] `frontend/src/components/RightPanel.tsx` — card list, fade-in stagger, skeleton
- [x] `frontend/src/App.tsx` — IDLE/ACTIVE layout switch, mouse wake, WS integration

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
