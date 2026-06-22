"""Tests for backend/api/routes.py — /health, /history, /preferences.

Each test uses:
  - A temporary SQLite database (via tmp_path) so no real jarvis.db is touched.
  - A temporary preferences JSON file so no real agent_data is read.
  - starlette TestClient for synchronous HTTP calls.
"""

import json
from contextlib import contextmanager
from datetime import UTC, datetime
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from starlette.testclient import TestClient

from backend.api import routes
from backend.db.models import Base, DbQuery, DbResult, DbSession
from backend.state import JarvisStatus


# ─── Shared fixtures ──────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_db(tmp_path):
    """Return a (engine, SessionFactory) backed by a temp SQLite file."""
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False},
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return engine, Session


@pytest.fixture()
def test_client(tmp_path, tmp_db):
    """FastAPI TestClient wired to isolated DB and prefs file."""
    _, Session = tmp_db
    prefs_file = tmp_path / "prefs.json"

    @contextmanager
    def _get_test_db():
        db = Session()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    app = FastAPI()
    app.include_router(routes.router)

    with patch("backend.api.routes.get_db", _get_test_db), \
         patch("backend.api.routes._PREFS_FILE", prefs_file):
        yield TestClient(app)


# ─── /health ─────────────────────────────────────────────────────────────────

def test_health_status_ok(test_client):
    resp = test_client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"


def test_health_includes_state(test_client):
    """state field reflects the current JarvisStatus value."""
    resp = test_client.get("/health")
    body = resp.json()
    assert "state" in body
    # Value must be a valid JarvisStatus
    assert body["state"] in {s.value for s in JarvisStatus}


# ─── /history ────────────────────────────────────────────────────────────────

def test_history_empty_db(test_client):
    resp = test_client.get("/history")
    assert resp.status_code == 200
    assert resp.json() == {"sessions": []}


def test_history_returns_sessions(tmp_path, tmp_db):
    """Sessions with nested queries and results appear in the response."""
    _, Session = tmp_db
    prefs_file = tmp_path / "prefs.json"

    @contextmanager
    def _get_test_db():
        db = Session()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    # Seed the database
    with _get_test_db() as db:
        sess = DbSession(started_at=datetime.now(UTC))
        db.add(sess)
        db.flush()
        q = DbQuery(session_id=sess.id, text="what time is it?", timestamp=datetime.now(UTC))
        db.add(q)
        db.flush()
        r = DbResult(
            query_id=q.id,
            title="Time card",
            url="https://example.com",
            snippet="It is noon.",
            source="example.com",
            position=0,
        )
        db.add(r)

    app = FastAPI()
    app.include_router(routes.router)

    with patch("backend.api.routes.get_db", _get_test_db), \
         patch("backend.api.routes._PREFS_FILE", prefs_file):
        client = TestClient(app)
        resp = client.get("/history")

    assert resp.status_code == 200
    data = resp.json()
    assert len(data["sessions"]) == 1
    session_data = data["sessions"][0]
    assert "id" in session_data
    assert len(session_data["queries"]) == 1
    assert session_data["queries"][0]["text"] == "what time is it?"
    assert session_data["queries"][0]["results"][0]["title"] == "Time card"
    assert session_data["queries"][0]["results"][0]["url"] == "https://example.com"


def test_history_limit_param(tmp_path, tmp_db):
    """?limit= caps the number of sessions returned."""
    _, Session = tmp_db
    prefs_file = tmp_path / "prefs.json"

    @contextmanager
    def _get_test_db():
        db = Session()
        try:
            yield db
            db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    with _get_test_db() as db:
        for i in range(5):
            db.add(DbSession(started_at=datetime.now(UTC)))

    app = FastAPI()
    app.include_router(routes.router)

    with patch("backend.api.routes.get_db", _get_test_db), \
         patch("backend.api.routes._PREFS_FILE", prefs_file):
        client = TestClient(app)
        resp = client.get("/history?limit=2")

    assert resp.status_code == 200
    assert len(resp.json()["sessions"]) == 2


# ─── /preferences ─────────────────────────────────────────────────────────────

def test_get_preferences_returns_defaults(test_client):
    resp = test_client.get("/preferences")
    assert resp.status_code == 200
    body = resp.json()
    assert body == {"topics": "", "name": "sir"}


def test_post_preferences_upserts_key(test_client):
    resp = test_client.post("/preferences", json={"key": "name", "value": "boss"})
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}

    resp = test_client.get("/preferences")
    assert resp.json()["name"] == "boss"


def test_post_preferences_adds_new_key(test_client):
    resp = test_client.post("/preferences", json={"key": "language", "value": "en"})
    assert resp.status_code == 200

    resp = test_client.get("/preferences")
    assert resp.json()["language"] == "en"
    # Existing defaults are preserved
    assert resp.json()["name"] == "sir"


def test_post_preferences_overwrites_existing_key(test_client):
    test_client.post("/preferences", json={"key": "topics", "value": "AI"})
    test_client.post("/preferences", json={"key": "topics", "value": "AI, science"})

    resp = test_client.get("/preferences")
    assert resp.json()["topics"] == "AI, science"
