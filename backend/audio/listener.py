import sys
import time

import numpy as np
import sounddevice as sd

from backend.config import (
    LISTEN_TIMEOUT_S,
    SILENCE_FRAMES,
    SILENCE_THRESHOLD,
    SPEECH_THRESHOLD,
)
from backend.state import message_queue

# Must match the blocksize used by the sounddevice InputStream (80ms @ 16kHz).
CHUNK = 1280


def _put(loop, msg: dict) -> None:
    """Thread-safe enqueue onto the asyncio message queue."""
    loop.call_soon_threadsafe(message_queue.put_nowait, msg)


def listen(stream: sd.InputStream, loop, whisper_model) -> str:
    """
    VAD-based speech capture followed by Whisper transcription.

    Reads CHUNK frames from the already-open InputStream, emits amplitude
    messages, and returns the transcribed text.  Returns "" on 10s timeout
    (no speech detected) or transcription failure.
    """
    speech_started = False
    silence_count = 0
    audio_buffer: list[np.ndarray] = []
    start_time = time.monotonic()

    try:
        while True:
            # Timeout: 10s with no speech → signal caller to say goodbye
            if not speech_started and (time.monotonic() - start_time) > LISTEN_TIMEOUT_S:
                return ""

            data, _ = stream.read(CHUNK)
            # Normalise int16 PCM to [-1, 1] float32 for RMS and Whisper
            frame = data.flatten().astype(np.float32) / 32768.0
            rms = float(np.sqrt(np.mean(np.square(frame))))

            _put(loop, {"type": "amplitude", "payload": {"value": rms}})

            if rms > SPEECH_THRESHOLD:
                speech_started = True
                silence_count = 0
                audio_buffer.append(frame)
            elif speech_started:
                audio_buffer.append(frame)
                if rms < SILENCE_THRESHOLD:
                    silence_count += 1
                    if silence_count >= SILENCE_FRAMES:
                        break
                # intermediate zone: accumulate but don't advance silence counter
    except Exception as exc:
        print(f"[listener] capture error: {exc}", file=sys.stderr)
        return ""

    if not audio_buffer:
        return ""

    try:
        audio_array = np.concatenate(audio_buffer)  # already normalised to [-1, 1]
        result = whisper_model.transcribe(audio_array, fp16=False)
        return result["text"].strip()
    except Exception as exc:
        print(f"[listener] transcription error: {exc}", file=sys.stderr)
        return ""
