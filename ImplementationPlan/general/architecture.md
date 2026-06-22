# General Architecture

This is the shared contract between the backend and frontend.
Read it before touching either codebase.

---

## System Component Diagram

```
┌──────────────────────────────────────────────────────────────────┐
│  Windows Machine                                                 │
│                                                                  │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Python Process (uv run uvicorn backend.main:app)         │  │
│  │                                                           │  │
│  │  ┌─────────────┐     asyncio.Queue                        │  │
│  │  │ Audio Thread │ ─────────────────────────────────┐      │  │
│  │  │             │                                   │      │  │
│  │  │ pvrecorder  │                                   ▼      │  │
│  │  │ Porcupine   │                    ┌──────────────────┐  │  │
│  │  │ Whisper STT │                    │  FastAPI App     │  │  │
│  │  │ edge-tts    │                    │                  │  │  │
│  │  │ sounddevice │                    │  GET /ws         │  │  │
│  │  └─────────────┘                    │  GET /health     │  │  │
│  │                                     │  GET /history    │  │  │
│  │  ┌─────────────┐                    │  GET /preferences│  │  │
│  │  │ DeepAgent   │◄──────────────────►│  POST /preferences  │  │
│  │  │ gemini-flash│                    │                  │  │  │
│  │  │ Tavily      │                    │  StaticFiles     │  │  │
│  │  └─────────────┘                    │  (frontend/dist) │  │  │
│  │                                     └───────┬──────────┘  │  │
│  │  ┌─────────────┐                            │             │  │
│  │  │  SQLite DB  │◄───────────────────────────┘             │  │
│  │  └─────────────┘                            │ WS + HTTP   │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                 │                │
│  ┌──────────────────────────────────────────────▼────────────┐  │
│  │  Browser (React + Vite)                                   │  │
│  │  SphereCanvas · LeftPanel · RightPanel · WaveformCanvas   │  │
│  └───────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────┘
```

---

## State Machine

```
STANDBY ──── wake word detected ────► GREETING
                                          │
                               TTS: "Hello sir..."
                                          │
                                          ▼
                                      LISTENING ──── 10s no speech ──► STANDBY
                                          │
                               speech + 1.5s silence
                                          │
                                          ▼
                                     PROCESSING
                                          │
                                 DeepAgent runs
                                          │
                                          ▼
                                     RESPONDING
                                          │
                          TTS summary + WS pushes results
                                          │
                                          ▼
                                   ACTIVE_WINDOW ──── 30s silence ──► STANDBY
                                          │
                                 follow-up utterance
                                          │
                              ┌───────────┴──────────┐
                              │                      │
                    "open X" pattern           any other query
                              │                      │
                    open_result() locally      back to PROCESSING
```

### State Timeout Summary

| State | Timeout | Action |
|---|---|---|
| `LISTENING` | 10s of silence after greeting | TTS: "Goodbye sir" → `STANDBY` |
| `ACTIVE_WINDOW` | 30s of no follow-up | silent → `STANDBY` |
| All states | Gemini/Tavily API error | safe default response, stay in flow |

---

## Data Flow

### Wake word → Response (full pipeline)

```
1. pvrecorder reads PCM frames continuously (16kHz, 512 samples/frame)
2. Porcupine.process(frame) → -1 (no match) or ≥0 (keyword index)
3. On match → put state_change:GREETING on asyncio.Queue
4. edge-tts generates WAV → sounddevice plays greeting
5. put state_change:LISTENING on queue
6. pvrecorder frames → RMS computed per frame
   ├── put amplitude:{value} on queue every frame (~50ms)
   └── VAD: accumulate audio_buffer until 1.5s silence
7. whisper_model.transcribe(audio_buffer, fp16=False) → transcript text
8. put transcript:{text} on queue
9. put state_change:PROCESSING on queue
10. Check OPEN_PATTERN against transcript
    ├── match → open_result(utterance, state.results) → webbrowser.open()
    └── no match → await agent.ainvoke(...) → parse JSON response
11. put state_change:RESPONDING on queue
12. put results:{items} on queue → WS broadcasts to browser
13. edge-tts speaks spoken_summary → sounddevice plays
14. put tts_text:{text} on queue
15. put state_change:ACTIVE_WINDOW on queue
16. 30s timer → put state_change:STANDBY on queue
```

### Thread / Async Boundary

```
Audio Thread (blocking)             FastAPI Event Loop (async)
───────────────────────             ──────────────────────────
pvrecorder.read()                   asyncio.Queue
porcupine.process()       ──►       │
RMS computation                     queue.put_nowait() via
whisper.transcribe()      ──►       loop.call_soon_threadsafe()
sounddevice.play()                  │
                                    ▼
                            api/websocket.py consumer loop
                            await queue.get() → ws.send_json()
```

---

## WebSocket API Contract

**Endpoint:** `GET /ws`
**Protocol:** single typed envelope

```json
{ "type": "<message_type>", "payload": { ... } }
```

| `type` | `payload` shape | Sent when |
|---|---|---|
| `state_change` | `{"state": "LISTENING"}` | Every state transition |
| `transcript` | `{"text": "what is..."}` | After Whisper transcribes |
| `results` | `{"items": [...]}` | After agent returns cards |
| `amplitude` | `{"value": 0.42}` | Every ~50ms during LISTENING + RESPONDING |
| `tts_text` | `{"text": "Here are the results..."}` | When Jarvis begins speaking |

**`results.items` item shape:**
```json
{
  "title":   "string — article headline or answer heading",
  "url":     "string — link URL, empty string for knowledge answers",
  "snippet": "string — 1-2 sentence summary",
  "source":  "string — domain name or 'Jarvis'"
}
```

---

## REST API Contract

All endpoints served by FastAPI at `http://localhost:8000`.

### `GET /health`
```json
{ "status": "ok", "state": "STANDBY" }
```

### `GET /history?limit=20`
```json
{
  "sessions": [
    {
      "id": 1,
      "started_at": "2026-06-21T10:00:00",
      "queries": [
        {
          "text": "what is the latest AI news?",
          "timestamp": "2026-06-21T10:00:05",
          "results": [{ "title": "...", "url": "...", "snippet": "...", "source": "..." }]
        }
      ]
    }
  ]
}
```

### `GET /preferences`
```json
{ "topics": "AI, biotech", "name": "sir" }
```

### `POST /preferences`
Request: `{ "key": "topics", "value": "AI, biotech, football" }`
Response: `{ "status": "ok" }`

---

## SQLite Schema

```
sessions
  id          INTEGER PRIMARY KEY
  started_at  DATETIME NOT NULL
  ended_at    DATETIME

queries
  id          INTEGER PRIMARY KEY
  session_id  INTEGER NOT NULL → sessions.id
  text        TEXT NOT NULL
  timestamp   DATETIME NOT NULL
  search_mode TEXT  -- "news" | "general" | "knowledge"

results
  id          INTEGER PRIMARY KEY
  query_id    INTEGER NOT NULL → queries.id
  title       TEXT NOT NULL
  url         TEXT NOT NULL
  snippet     TEXT NOT NULL
  source      TEXT NOT NULL
  position    INTEGER NOT NULL  -- 0-4, card order

preferences
  id          INTEGER PRIMARY KEY
  key         TEXT NOT NULL UNIQUE
  value       TEXT NOT NULL
```

---

## URL Configuration (Dev vs Prod)

### Development
- Backend: `http://localhost:8000`
- Frontend dev server: `http://localhost:5173`
- `vite.config.ts` proxies `/ws` → `http://localhost:8000`:
  ```ts
  server: { proxy: { '/ws': { target: 'http://localhost:8000', ws: true } } }
  ```
- Frontend WS URL: `ws://${window.location.host}/ws` → proxied to backend

### Production
- FastAPI serves built React bundle via `StaticFiles(directory="frontend/dist")`
- Both on `http://localhost:8000`
- Frontend WS URL: `ws://${window.location.host}/ws` → resolves directly
- **No code changes needed when deploying** — relative URL adapts to any host

---

## Error Handling Strategy

| Component | Failure | Behaviour |
|---|---|---|
| Porcupine | Invalid access key | Log to stderr on startup, exit with clear message |
| Whisper | Transcription fails | Return empty string, loop back to LISTENING |
| Gemini API | Timeout / rate limit | Return safe default response dict, TTS the error |
| Tavily | Search fails | Return JSON error string, agent falls back to knowledge |
| edge-tts | Network unavailable | Log to stderr, skip TTS, pipeline continues silently |
| sounddevice | Audio device error | Log to stderr, skip playback, pipeline continues |
| WebSocket | Client disconnects | Clear connection ref, drop queue messages until reconnect |
| SQLite | Write fails | Log to stderr, skip DB write — voice pipeline unaffected |

**Rule:** no single component failure should crash the pipeline. Every module wraps its work in `try/except` and returns a safe default.

---

## Verification

1. Read this document before implementing any module
2. After backend starts: open DevTools → Network → WS → verify all 5 message types and payload shapes match this contract exactly
3. In dev: confirm Vite proxy forwards `/ws` correctly (`ws://localhost:5173/ws` → `ws://localhost:8000/ws`)
4. In prod: confirm `window.location.host` resolves to `localhost:8000`
5. `uv run pytest` + `npm run test` — both pass with mocked audio and LLM
