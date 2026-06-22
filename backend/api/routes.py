import json
import sys
from datetime import datetime

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from backend.config import AGENT_DATA_DIR
from backend.db.database import get_db
from backend.db.models import DbQuery, DbResult, DbSession
from backend.state import state

router = APIRouter()

_PREFS_FILE = AGENT_DATA_DIR / "preferences.json"


def _load_prefs() -> dict:
    """Read preferences from disk; return defaults on any error."""
    if _PREFS_FILE.exists():
        try:
            return json.loads(_PREFS_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    return {"topics": "", "name": "sir"}


def _save_prefs(prefs: dict) -> None:
    """Persist preferences dict to disk."""
    try:
        _PREFS_FILE.parent.mkdir(parents=True, exist_ok=True)
        _PREFS_FILE.write_text(json.dumps(prefs, indent=2), encoding="utf-8")
    except Exception as exc:
        print(f"[routes] failed to save preferences: {exc}", file=sys.stderr)


@router.get("/health")
async def health() -> JSONResponse:
    """Return server liveness and current Jarvis state."""
    return JSONResponse({"status": "ok", "state": state.status.value})


@router.get("/history")
async def history(limit: int = 20) -> JSONResponse:
    """Return the last `limit` sessions with their queries and results."""
    try:
        with get_db() as db:
            sessions = (
                db.query(DbSession)
                .order_by(DbSession.started_at.desc())
                .limit(limit)
                .all()
            )
            data = []
            for session in sessions:
                queries = []
                for q in sorted(session.queries, key=lambda x: x.timestamp):
                    results = [
                        {
                            "title": r.title,
                            "url": r.url,
                            "snippet": r.snippet,
                            "source": r.source,
                        }
                        for r in sorted(q.results, key=lambda x: x.position)
                    ]
                    queries.append(
                        {
                            "text": q.text,
                            "timestamp": q.timestamp.isoformat(),
                            "results": results,
                        }
                    )
                data.append(
                    {
                        "id": session.id,
                        "started_at": session.started_at.isoformat(),
                        "queries": queries,
                    }
                )
        return JSONResponse({"sessions": data})
    except Exception as exc:
        print(f"[routes] history error: {exc}", file=sys.stderr)
        return JSONResponse({"sessions": []})


@router.get("/preferences")
async def get_preferences() -> JSONResponse:
    """Return the current user preferences dict."""
    return JSONResponse(_load_prefs())


class PrefUpdate(BaseModel):
    key: str
    value: str


@router.post("/preferences")
async def post_preferences(body: PrefUpdate) -> JSONResponse:
    """Upsert a single preference key."""
    prefs = _load_prefs()
    prefs[body.key] = body.value
    _save_prefs(prefs)
    return JSONResponse({"status": "ok"})
