import asyncio
import re
import sys
import tempfile
from pathlib import Path

import edge_tts
import sounddevice as sd
import soundfile as sf

from backend.config import TTS_VOICE

# Splits on sentence boundaries so each sentence is synthesised and played
# independently — the user hears the first sentence after ~0.3s instead of
# waiting for the full response to be generated.
_SENTENCE_RE = re.compile(r'(?<=[.!?])\s+')


def speak(text: str) -> None:
    """Split text into sentences and play each one as soon as it is synthesised."""
    sentences = [s for s in _SENTENCE_RE.split(text.strip()) if s]
    if not sentences:
        return
    for sentence in sentences:
        _speak_one(sentence)


def _speak_one(text: str) -> None:
    """Synthesise and play a single sentence. Skips silently on any error."""
    try:
        asyncio.run(_synthesize_and_play(text))
    except Exception as exc:
        print(f"[speaker] TTS failed: {exc}", file=sys.stderr)


async def _synthesize_and_play(text: str) -> None:
    """Generate audio via edge-tts, write to temp MP3, decode, play, delete."""
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
