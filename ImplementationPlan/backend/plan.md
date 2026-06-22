# Backend Implementation Plan

## Confirmed Design Decisions

| Concern | Decision |
|---|---|
| Audio daemon | `threading.Thread` started at FastAPI lifespan, bridges to async via `asyncio.Queue` |
| Mic capture | `sounddevice` — captures 80ms frames for openWakeWord + VAD |
| End-of-speech | Silence-based VAD: RMS energy per frame, 1.5s silence → stop recording |
| TTS playback | `edge-tts` → WAV temp file → `sounddevice` (no ffmpeg, no browser) |
| Waveform data | Backend streams RMS float via WS `amplitude` message every ~50ms |
| WebSocket protocol | Single typed envelope `{"type": "...", "payload": {...}}`, 5 message types |
| SQLAlchemy | Sync engine + `run_in_executor` when called from async handlers |
| System prompt | Loaded from `backend/prompts/system.md` file at startup — not hardcoded |
| Follow-up routing | Local regex/difflib check first → handle open commands; everything else → DeepAgent |
| DeepAgent memory | `AGENTS.md` via `FilesystemBackend` — replaces SQLite `preferences` table |
| DeepAgent checkpointer | `MemorySaver` — required for multi-turn follow-up in ACTIVE_WINDOW |
| Config architecture | `config.py` typed constants + `backend/prompts/` directory for all text |

---

## Folder Structure

```
backend/
├── __init__.py
├── main.py              # FastAPI app + lifespan + static file serving
├── config.py            # typed constants loaded from .env + defaults
├── state.py             # JarvisStatus enum, JarvisState dataclass, shared asyncio.Queue
├── prompts/
│   ├── system.md        # DeepAgent system prompt (loaded at startup)
│   ├── greeting.txt     # "Hello sir, how can I help you today?"
│   └── goodbye.txt      # "Goodbye sir."
├── agent_data/
│   └── memories/
│       └── AGENTS.md    # DeepAgent persistent memory (auto-created, agent-managed)
├── audio/
│   ├── __init__.py
│   ├── wake_word.py     # Porcupine + pvrecorder loop; puts events on queue
│   ├── listener.py      # VAD (RMS) capture + Whisper transcription
│   └── speaker.py       # edge-tts → WAV temp file → sounddevice playback
├── agent/
│   ├── __init__.py
│   ├── jarvis_agent.py  # DeepAgent: FilesystemBackend + MemorySaver + tools
│   └── tools/
│       ├── __init__.py
│       ├── search.py        # tavily_search(query, mode) — plain callable
│       ├── browser.py       # open_result(utterance, results) — called by pipeline, not agent
│       └── datetime_tool.py # tell_time_date() — plain callable
├── api/
│   ├── __init__.py
│   ├── websocket.py     # WS endpoint; consumes queue, broadcasts to connected client
│   └── routes.py        # REST: GET /health, GET /history, GET+POST /preferences
└── db/
    ├── __init__.py
    ├── database.py      # SQLAlchemy sync engine + SessionLocal factory
    └── models.py        # Session, Query, Result ORM models (preferences removed)
```

---

## pyproject.toml Dependencies

```toml
[project]
name = "jarvis"
version = "0.1.0"
requires-python = ">=3.11"
dependencies = [
    "fastapi",
    "uvicorn[standard]",
    "pvporcupine",
    "pvrecorder",
    "openai-whisper",
    "edge-tts",
    "sounddevice",
    "numpy",
    "deepagents",
    "langchain-google-genai",
    "tavily-python",
    "sqlalchemy",
    "python-dotenv",
    "websockets",
    "pytest",
    "pytest-asyncio",
]
```

---

## Module-by-Module Plan

### `config.py`
- Load all env vars from `.env` via `python-dotenv`
- Export typed constants grouped by concern:
  ```python
  from pathlib import Path

  # --- API ---
  PICOVOICE_ACCESS_KEY = os.getenv("PICOVOICE_ACCESS_KEY")
  GEMINI_API_KEY       = os.getenv("GEMINI_API_KEY")
  TAVILY_API_KEY       = os.getenv("TAVILY_API_KEY")
  MODEL_AGENT          = os.getenv("MODEL_AGENT", "google_genai:gemini-2.0-flash")

  # --- Server ---
  BACKEND_HOST = os.getenv("BACKEND_HOST", "127.0.0.1")
  BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

  # --- Audio ---
  WHISPER_MODEL      = os.getenv("WHISPER_MODEL", "base")
  TTS_VOICE          = os.getenv("TTS_VOICE", "en-GB-RyanNeural")
  WAKE_WORD_THRESHOLD = float(os.getenv("WAKE_WORD_THRESHOLD", "0.5"))
  SPEECH_THRESHOLD   = float(os.getenv("SPEECH_THRESHOLD", "0.02"))
  SILENCE_THRESHOLD  = float(os.getenv("SILENCE_THRESHOLD", "0.01"))
  SILENCE_FRAMES     = int(os.getenv("SILENCE_FRAMES", "24"))   # 1.5s @ ~16fps
  LISTEN_TIMEOUT_S   = int(os.getenv("LISTEN_TIMEOUT_S", "10"))
  ACTIVE_WINDOW_S    = int(os.getenv("ACTIVE_WINDOW_S", "30"))

  # --- Paths ---
  PROMPTS_DIR    = Path(os.getenv("PROMPTS_DIR",    "backend/prompts"))
  AGENT_DATA_DIR = Path(os.getenv("AGENT_DATA_DIR", "backend/agent_data"))
  SESSION_RECALL_WINDOW = int(os.getenv("SESSION_RECALL_WINDOW", "7200"))
  ```
- `def load_prompt(filename: str) -> str` — reads `PROMPTS_DIR / filename`, raises on missing

### `state.py`
- `JarvisStatus` enum: `STANDBY`, `GREETING`, `LISTENING`, `PROCESSING`, `RESPONDING`, `ACTIVE_WINDOW`
- `JarvisState` dataclass: `status`, `transcript`, `results` (list of result dicts), `preferences` (dict)
- One module-level `asyncio.Queue` instance imported everywhere it is needed
- Audio thread writes via `loop.call_soon_threadsafe(queue.put_nowait, msg)`

### `audio/wake_word.py`
- Init `openwakeword.Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")`
- Mic capture via `sounddevice.InputStream(samplerate=16000, channels=1, dtype="int16", blocksize=1280)`
  - `CHUNK = 1280` → 80ms frames at 16kHz, the frame size openWakeWord expects
- Blocking loop: `stream.read(CHUNK)` → `oww.predict(audio.flatten())` → check `score["hey_jarvis"] >= WAKE_WORD_THRESHOLD`
- On detection: `oww.reset()` (prevent re-triggering), then put `{"type": "state_change", "payload": {"state": "GREETING"}}` on queue
- Call `speaker.speak(greeting_text)` then signal transition to LISTENING state

### `audio/listener.py`
- Continue reading `pvrecorder` frames after wake word fires
- Per frame: `rms = np.sqrt(np.mean(np.square(np.array(frame, dtype=np.float32))))`
- Send `{"type": "amplitude", "payload": {"value": float(rms)}}` on queue every frame (~50ms)
- VAD state machine:
  - `speech_started = False`, `silence_frames = 0`, `audio_buffer = []`
  - `rms > SPEECH_THRESHOLD` → set `speech_started = True`, reset `silence_frames`
  - `speech_started` and `rms < SILENCE_THRESHOLD` → increment `silence_frames`
  - `silence_frames >= SILENCE_FRAME_COUNT` (1.5s worth) → stop, return buffer
  - No speech for 10s → timeout → put `{"type": "state_change", "payload": {"state": "STANDBY"}}`
- On buffer ready: pass `np.array(buffer, dtype=np.float32)` directly to `whisper_model.transcribe(array, fp16=False)`
- Put `{"type": "transcript", "payload": {"text": transcript}}` on queue

### `audio/speaker.py`
- `async def speak(text: str) -> None`
- Use `edge-tts` with `Communicate(text, voice=TTS_VOICE)` to save audio as `.wav` to a temp file
  (edge-tts supports WAV output — avoids MP3 decoding entirely)
- `sounddevice.play(data, samplerate)` then `sounddevice.wait()` to block until done
- Delete temp file after playback
- Wrap in try/except — on failure log to stderr, do not crash the pipeline

### `agent/jarvis_agent.py`
- `create_deep_agent` returns a `CompiledStateGraph` — supports `.ainvoke()`
- Model string: `MODEL_AGENT` from `config.py` (default `"google_genai:gemini-2.0-flash"`)
- System prompt: loaded from `backend/prompts/system.md` via `config.load_prompt("system.md")`
- `FilesystemBackend(root_dir=str(AGENT_DATA_DIR))` — persists AGENTS.md to disk
- `MemorySaver()` checkpointer — enables multi-turn follow-up in ACTIVE_WINDOW
- `memory=["/memories/AGENTS.md"]` — agent reads/writes its own preference file
- Tools: `[tavily_search, tell_time_date]` as plain callables
  - `browser.open_result` is NOT a DeepAgent tool — handled locally before agent is called
  - DeepAgent built-ins (`write_todos`, `ls`, etc.) are injected but won't be invoked for Jarvis queries

```python
from deepagents import create_deep_agent
from deepagents.backends.filesystem import FilesystemBackend
from langgraph.checkpoint.memory import MemorySaver
from backend.config import MODEL_AGENT, AGENT_DATA_DIR, load_prompt
from backend.agent.tools.search import tavily_search
from backend.agent.tools.datetime_tool import tell_time_date

_backend     = FilesystemBackend(root_dir=str(AGENT_DATA_DIR))
_checkpointer = MemorySaver()
_agent = create_deep_agent(
    model=MODEL_AGENT,
    tools=[tavily_search, tell_time_date],
    system_prompt=load_prompt("system.md"),
    memory=["/memories/AGENTS.md"],
    backend=_backend,
    checkpointer=_checkpointer,
)
```

- `async def run(query: str, thread_id: str) -> dict`:
  1. `result = await _agent.ainvoke({"messages": [{"role": "user", "content": query}]}, config={"configurable": {"thread_id": thread_id}})`
  2. `raw_text = result["messages"][-1].content`
  3. Extract JSON block with `re.search(r'```json\s*(.*?)\s*```', raw_text, re.DOTALL)`
  4. `json.loads(match.group(1))` → return dict
  5. On any failure → return `{"spoken_summary": "I'm sorry sir, I encountered an error.", "items": []}`
- `thread_id` is a session UUID generated at wake-word detection, reused for the full ACTIVE_WINDOW

### `agent/tools/search.py`
```python
def tavily_search(query: str, mode: str = "general") -> str:
    """Search the web. Use mode='news' for current events, 'general' for factual queries."""
    ...
```
- `TavilyClient(api_key=TAVILY_API_KEY).search(query, search_depth=mode, max_results=5)`
- Return `json.dumps(results)` on success, `json.dumps({"error": str(e)})` on failure

### `agent/tools/browser.py`
- Called directly by the audio pipeline during ACTIVE_WINDOW, NOT a DeepAgent tool
```python
def open_result(utterance: str, results: list[dict]) -> str:
    """Open a result card URL in the default browser by index or name reference."""
    ...
```
- Regex: `re.search(r"\b(one|1|two|2|three|3|four|4|five|5)\b", utterance, re.I)` → map to 0-based index
- Fallback: `difflib.get_close_matches(utterance, [r["title"] for r in results], n=1, cutoff=0.3)`
- `webbrowser.open(url)` → return `f"Opening {title}, sir."`
- Return `"I couldn't find that result, sir."` if no match

### `agent/tools/datetime_tool.py`
```python
def tell_time_date() -> str:
    """Return the current date and time."""
    return datetime.now().strftime("It is %A, %B %d %Y, %H:%M")
```

### `api/websocket.py`
- `GET /ws` WebSocket endpoint
- Store single active connection reference
- Consumer loop: `while True: msg = await queue.get(); await websocket.send_json(msg)`
- On disconnect: clear connection reference, stop loop

### `api/routes.py`
- `GET /health` → `{"status": "ok", "state": current_status.value}`
- `GET /history?limit=20` → last N sessions with queries + results from SQLite
- `GET /preferences` → current preferences dict
- `POST /preferences` body `{"key": str, "value": str}` → upsert in SQLite

### `db/models.py`
Three tables (preferences removed — handled by DeepAgent's AGENTS.md):
```
sessions:  id (PK), started_at, ended_at
queries:   id (PK), session_id (FK), text, timestamp, search_mode
results:   id (PK), query_id (FK), title, url, snippet, source, position
```

### `db/database.py`
- `engine = create_engine("sqlite:///./jarvis.db", connect_args={"check_same_thread": False})`
- `SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)`
- `get_db()` context manager for use with `run_in_executor`

### `main.py`
- FastAPI `lifespan` context manager:
  1. `Base.metadata.create_all(engine)`
  2. `whisper_model = whisper.load_model(WHISPER_MODEL)` (cached globally)
  3. Session recall: query last session, load results if within `SESSION_RECALL_WINDOW` seconds
  4. Capture event loop: `loop = asyncio.get_event_loop()`
  5. `threading.Thread(target=audio_loop, args=(loop, whisper_model), daemon=True).start()`
- `app.mount("/", StaticFiles(directory="frontend/dist", html=True))`
- Include routers from `api/routes.py` and `api/websocket.py`

---

## Key Cross-Cutting Patterns

### Asyncio Bridge (audio thread → WebSocket)
```python
# Audio thread (blocking context):
loop.call_soon_threadsafe(message_queue.put_nowait, {"type": "amplitude", "payload": {"value": rms}})

# WebSocket handler (async context):
while True:
    msg = await message_queue.get()
    await websocket.send_json(msg)
```
`loop` is captured at startup in `main.py` and passed to the audio thread.

### WebSocket Message Types
| `type` | `payload` | When |
|---|---|---|
| `state_change` | `{"state": "LISTENING"}` | Every state transition |
| `transcript` | `{"text": "..."}` | After Whisper transcribes |
| `results` | `{"items": [...]}` | After agent returns cards |
| `amplitude` | `{"value": 0.42}` | Every frame during LISTENING/RESPONDING |
| `tts_text` | `{"text": "..."}` | When Jarvis begins speaking |

### Follow-up Routing (ACTIVE_WINDOW)
```python
OPEN_PATTERN = re.compile(r"\bopen\b.*(one|two|three|four|five|\d+)", re.IGNORECASE)

if OPEN_PATTERN.search(utterance):
    msg = open_result(utterance, state.results)  # local, instant
else:
    result = await agent.run(utterance, state)   # DeepAgent
```

### Session Recall
```python
with SessionLocal() as db:
    last = db.query(DbSession).order_by(DbSession.started_at.desc()).first()
    if last and (datetime.now() - last.ended_at).seconds < SESSION_RECALL_WINDOW:
        state.results = load_last_results(db, last.id)
```

---

## Verification

1. `uv sync` — installs all deps with no errors
2. Fill `.env` with real API keys (Picovoice, Gemini, Tavily)
3. `uv run uvicorn backend.main:app --reload` — server starts, no import errors
4. Say "Jarvis" → terminal logs wake word detection
5. Jarvis speaks greeting through speakers
6. Speak a query → Whisper transcribes → agent returns results → cards visible via WS
7. Check browser DevTools → Network → WS → confirm all 5 message types appear correctly
8. `uv run pytest` — all unit tests pass (LLM + audio mocked)
