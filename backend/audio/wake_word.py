import asyncio
import re
import sys
import uuid
from datetime import datetime

import openwakeword
import sounddevice as sd

from backend.agent import jarvis_agent
from backend.agent.tools.browser import open_result
from backend.audio.listener import CHUNK, listen
from backend.audio.speaker import speak
from backend.config import ACTIVE_WINDOW_S, WAKE_WORD_THRESHOLD, load_prompt
from backend.db.database import get_db
from backend.db.models import DbQuery, DbResult, DbSession
from backend.state import JarvisStatus, message_queue, state

# Matches "open (one/1/two/2/…)" — handled locally without invoking the agent
OPEN_PATTERN = re.compile(r"\bopen\b.*(one|two|three|four|five|[1-5])\b", re.IGNORECASE)


def _put(loop: asyncio.AbstractEventLoop, msg: dict) -> None:
    """Thread-safe enqueue from the audio thread onto the asyncio queue."""
    loop.call_soon_threadsafe(message_queue.put_nowait, msg)


def _run_agent(loop: asyncio.AbstractEventLoop, query: str, thread_id: str) -> dict:
    """Block the audio thread until the async agent call completes."""
    future = asyncio.run_coroutine_threadsafe(
        jarvis_agent.run(query, thread_id), loop
    )
    return future.result()


def _save_query(db_session_id: int, text: str, items: list[dict]) -> None:
    """Persist a query and its result cards to SQLite."""
    try:
        with get_db() as db:
            q = DbQuery(
                session_id=db_session_id,
                text=text,
                timestamp=datetime.utcnow(),
                search_mode=None,
            )
            db.add(q)
            db.flush()  # get q.id before adding results
            for pos, item in enumerate(items):
                db.add(
                    DbResult(
                        query_id=q.id,
                        title=item.get("title", ""),
                        url=item.get("url", ""),
                        snippet=item.get("snippet", ""),
                        source=item.get("source", ""),
                        position=pos,
                    )
                )
    except Exception as exc:
        print(f"[wake_word] DB write error: {exc}", file=sys.stderr)


def _process_query(
    loop: asyncio.AbstractEventLoop,
    stream: sd.InputStream,
    whisper_model,
    transcript: str,
    thread_id: str,
    db_session_id: int,
) -> None:
    """
    Run the agent for one query, broadcast results, speak the summary, and
    persist to DB.  Called for both first queries and ACTIVE_WINDOW follow-ups.
    """
    state.status = JarvisStatus.PROCESSING
    state.transcript = transcript
    _put(loop, {"type": "transcript", "payload": {"text": transcript}})
    _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.PROCESSING.value}})

    response = _run_agent(loop, transcript, thread_id)

    items: list[dict] = response.get("items", [])
    spoken_summary: str = response.get(
        "spoken_summary", "I'm sorry sir, I encountered an error."
    )

    state.results = items

    # ── RESPONDING ───────────────────────────────────────────────────────────
    state.status = JarvisStatus.RESPONDING
    _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.RESPONDING.value}})
    _put(loop, {"type": "results", "payload": {"items": items}})
    _put(loop, {"type": "tts_text", "payload": {"text": spoken_summary}})

    speak(spoken_summary)

    _save_query(db_session_id, transcript, items)


def audio_loop(loop: asyncio.AbstractEventLoop, whisper_model) -> None:
    """
    Blocking audio loop — runs in a background daemon thread.

    Opens a single 16kHz sounddevice InputStream shared by the wake-word
    detector and the speech listener.  Full state machine:

        STANDBY → GREETING → LISTENING → PROCESSING → RESPONDING
                                                            │
                                                      ACTIVE_WINDOW ←─ follow-up
                                                            │
                                                         STANDBY
    """
    try:
        oww = openwakeword.Model(wakeword_models=["hey_jarvis"], inference_framework="onnx")
    except Exception as exc:
        print(f"[wake_word] failed to load openWakeWord model: {exc}", file=sys.stderr)
        return

    greeting = load_prompt("greeting.txt")
    goodbye  = load_prompt("goodbye.txt")

    try:
        with sd.InputStream(
            samplerate=16000,
            channels=1,
            dtype="int16",
            blocksize=CHUNK,
        ) as stream:
            print("[wake_word] listening for 'hey Jarvis'…", file=sys.stderr)

            while True:
                # ── STANDBY: feed frames to openWakeWord ──────────────────
                data, _ = stream.read(CHUNK)
                frame = data.flatten()
                scores = oww.predict(frame)

                if not any(v >= WAKE_WORD_THRESHOLD for v in scores.values()):
                    continue

                oww.reset()
                print("[wake_word] wake word detected", file=sys.stderr)

                # ── GREETING ─────────────────────────────────────────────
                state.status = JarvisStatus.GREETING
                _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.GREETING.value}})
                speak(greeting)

                # Create a DB session and a conversation thread_id for this interaction
                db_session_id: int | None = None
                try:
                    with get_db() as db:
                        db_session = DbSession(started_at=datetime.utcnow())
                        db.add(db_session)
                        db.flush()
                        db_session_id = db_session.id
                except Exception as exc:
                    print(f"[wake_word] failed to create DB session: {exc}", file=sys.stderr)

                thread_id = str(uuid.uuid4())

                # ── LISTENING ────────────────────────────────────────────
                state.status = JarvisStatus.LISTENING
                _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.LISTENING.value}})

                transcript = listen(stream, loop, whisper_model)

                if not transcript:
                    speak(goodbye)
                    _close_db_session(db_session_id)
                    state.status = JarvisStatus.STANDBY
                    _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.STANDBY.value}})
                    continue

                # ── PROCESSING → RESPONDING ───────────────────────────────
                _process_query(loop, stream, whisper_model, transcript, thread_id, db_session_id or 0)

                # ── ACTIVE_WINDOW ─────────────────────────────────────────
                state.status = JarvisStatus.ACTIVE_WINDOW
                _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.ACTIVE_WINDOW.value}})

                while True:
                    follow_up = listen(stream, loop, whisper_model, timeout_s=ACTIVE_WINDOW_S)

                    if not follow_up:
                        # 30s silence in ACTIVE_WINDOW → return to STANDBY silently
                        break

                    if OPEN_PATTERN.search(follow_up):
                        msg = open_result(follow_up, state.results)
                        speak(msg)
                        # Stay in ACTIVE_WINDOW; re-announce state so UI keeps waveform active
                        state.status = JarvisStatus.ACTIVE_WINDOW
                        _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.ACTIVE_WINDOW.value}})
                    else:
                        _process_query(loop, stream, whisper_model, follow_up, thread_id, db_session_id or 0)
                        state.status = JarvisStatus.ACTIVE_WINDOW
                        _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.ACTIVE_WINDOW.value}})

                _close_db_session(db_session_id)
                state.status = JarvisStatus.STANDBY
                _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.STANDBY.value}})

    except Exception as exc:
        print(f"[wake_word] audio loop crashed: {exc}", file=sys.stderr)


def _close_db_session(db_session_id: int | None) -> None:
    """Mark the DB session as ended."""
    if db_session_id is None:
        return
    try:
        with get_db() as db:
            session = db.get(DbSession, db_session_id)
            if session:
                session.ended_at = datetime.utcnow()
    except Exception as exc:
        print(f"[wake_word] failed to close DB session: {exc}", file=sys.stderr)
