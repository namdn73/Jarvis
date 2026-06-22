import asyncio
import sys
import threading
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import whisper
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.audio.wake_word import audio_loop
from backend.config import WHISPER_MODEL
from backend.db.database import init_db
from backend.state import state


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init DB, load Whisper, launch audio thread."""
    init_db()

    print(f"[main] loading Whisper model '{WHISPER_MODEL}'…", file=sys.stderr)
    whisper_model = whisper.load_model(WHISPER_MODEL)

    loop = asyncio.get_event_loop()
    threading.Thread(
        target=audio_loop,
        args=(loop, whisper_model),
        daemon=True,
    ).start()

    yield


app = FastAPI(title="Jarvis", lifespan=lifespan)


@app.get("/health")
async def health() -> JSONResponse:
    """Return server status and current Jarvis state."""
    return JSONResponse({"status": "ok", "state": state.status.value})
