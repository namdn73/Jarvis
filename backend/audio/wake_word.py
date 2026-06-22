import asyncio
import sys

import openwakeword
import sounddevice as sd

from backend.audio.listener import CHUNK, listen
from backend.audio.speaker import speak
from backend.config import WAKE_WORD_THRESHOLD, load_prompt
from backend.state import JarvisStatus, message_queue, state


def _put(loop: asyncio.AbstractEventLoop, msg: dict) -> None:
    """Thread-safe enqueue from the audio thread onto the asyncio queue."""
    loop.call_soon_threadsafe(message_queue.put_nowait, msg)


def audio_loop(loop: asyncio.AbstractEventLoop, whisper_model) -> None:
    """
    Blocking audio loop — runs in a background daemon thread.

    Opens a single 16kHz sounddevice InputStream shared by the wake-word
    detector and the speech listener.  State machine:

        STANDBY → GREETING → LISTENING → PROCESSING → STANDBY

    Agent invocation (PROCESSING → RESPONDING → ACTIVE_WINDOW) is wired in
    Sessions 4 and 5.
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
                frame = data.flatten()  # int16, shape (CHUNK,)
                scores = oww.predict(frame)

                if not any(v >= WAKE_WORD_THRESHOLD for v in scores.values()):
                    continue

                # Wake word detected — reset internal buffers to avoid re-trigger
                oww.reset()
                print("[wake_word] wake word detected", file=sys.stderr)

                # ── GREETING ─────────────────────────────────────────────
                state.status = JarvisStatus.GREETING
                _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.GREETING.value}})
                speak(greeting)

                # ── LISTENING ────────────────────────────────────────────
                state.status = JarvisStatus.LISTENING
                _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.LISTENING.value}})

                transcript = listen(stream, loop, whisper_model)

                if not transcript:
                    # 10s timeout with no speech
                    speak(goodbye)
                    state.status = JarvisStatus.STANDBY
                    _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.STANDBY.value}})
                    continue

                # ── PROCESSING ───────────────────────────────────────────
                state.status = JarvisStatus.PROCESSING
                state.transcript = transcript
                _put(loop, {"type": "transcript", "payload": {"text": transcript}})
                _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.PROCESSING.value}})

                # TODO (Sessions 4+5): run agent, broadcast results, speak response,
                # enter ACTIVE_WINDOW with 30s follow-up timer.
                # For now return to STANDBY immediately after transcription.
                state.status = JarvisStatus.STANDBY
                _put(loop, {"type": "state_change", "payload": {"state": JarvisStatus.STANDBY.value}})

    except Exception as exc:
        print(f"[wake_word] audio loop crashed: {exc}", file=sys.stderr)
