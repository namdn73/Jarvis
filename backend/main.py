import asyncio
import sys
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

import whisper
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from backend.agent import jarvis_agent
from backend.api import routes, websocket
from backend.audio.wake_word import audio_loop
from backend.config import WHISPER_MODEL
from backend.db.database import init_db
from backend.state import state


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: init DB, load Whisper, pre-warm agent, launch audio thread."""
    init_db()

    print(f"[main] loading Whisper model '{WHISPER_MODEL}'…", file=sys.stderr)
    whisper_model = whisper.load_model(WHISPER_MODEL)

    print("[main] pre-warming agent…", file=sys.stderr)
    try:
        await jarvis_agent.run("ping", "warmup")
        print("[main] agent warm", file=sys.stderr)
    except Exception as exc:
        print(f"[main] agent pre-warm failed (non-fatal): {exc}", file=sys.stderr)

    loop = asyncio.get_event_loop()
    threading.Thread(
        target=audio_loop,
        args=(loop, whisper_model),
        daemon=True,
    ).start()

    yield


app = FastAPI(title="Jarvis", lifespan=lifespan)

app.include_router(routes.router)
app.include_router(websocket.router)

# Serve the built React bundle in production; skip if not yet built
_dist = Path("frontend/dist")
if _dist.exists():
    app.mount("/", StaticFiles(directory=str(_dist), html=True), name="static")
