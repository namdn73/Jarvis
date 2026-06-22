from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from backend.db.database import init_db
from backend.state import state


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Startup: initialise DB. Shutdown: nothing to clean up yet."""
    init_db()
    yield


app = FastAPI(title="Jarvis", lifespan=lifespan)


@app.get("/health")
async def health() -> JSONResponse:
    """Return server status and current Jarvis state."""
    return JSONResponse({"status": "ok", "state": state.status.value})
