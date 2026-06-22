import asyncio
import sys
import tempfile
from pathlib import Path

import edge_tts
import sounddevice as sd
import soundfile as sf

from backend.config import TTS_VOICE


def speak(text: str) -> None:
    """Speak text via edge-tts through the system audio device. Blocks until done."""
    try:
        asyncio.run(_synthesize_and_play(text))
    except Exception as exc:
        print(f"[speaker] TTS failed: {exc}", file=sys.stderr)


async def _synthesize_and_play(text: str) -> None:
    """Synthesise audio with edge-tts, write to temp MP3, decode, and play."""
    tmp = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
    tmp_path = Path(tmp.name)
    tmp.close()
    try:
        await edge_tts.Communicate(text, voice=TTS_VOICE).save(str(tmp_path))
        data, samplerate = sf.read(str(tmp_path))
        sd.play(data, samplerate=samplerate)
        sd.wait()
    finally:
        tmp_path.unlink(missing_ok=True)
