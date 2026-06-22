"""Tests for the /ws WebSocket endpoint.

Uses starlette TestClient (synchronous) which handles the event loop internally.
The module-level message_queue is replaced with a test queue pre-loaded with
messages so the consumer loop has data to forward before the client disconnects.
"""

import asyncio
from unittest.mock import patch

import pytest
from fastapi import FastAPI
from starlette.testclient import TestClient

from backend.api import websocket as ws_module


def _make_app(queue: asyncio.Queue) -> FastAPI:
    app = FastAPI()
    app.include_router(ws_module.router)
    return app


def test_ws_broadcasts_single_message():
    """A message put on the queue is forwarded to the connected WS client."""
    q: asyncio.Queue = asyncio.Queue()
    q.put_nowait({"type": "state_change", "payload": {"state": "LISTENING"}})

    with patch("backend.api.websocket.message_queue", q):
        client = TestClient(_make_app(q))
        with client.websocket_connect("/ws") as ws:
            data = ws.receive_json()

    assert data["type"] == "state_change"
    assert data["payload"]["state"] == "LISTENING"


def test_ws_broadcasts_multiple_messages_in_order():
    """Multiple queued messages are delivered in insertion order."""
    q: asyncio.Queue = asyncio.Queue()
    messages = [
        {"type": "state_change", "payload": {"state": "GREETING"}},
        {"type": "transcript",   "payload": {"text": "Hello Jarvis"}},
        {"type": "amplitude",    "payload": {"value": 0.42}},
    ]
    for m in messages:
        q.put_nowait(m)

    with patch("backend.api.websocket.message_queue", q):
        client = TestClient(_make_app(q))
        with client.websocket_connect("/ws") as ws:
            received = [ws.receive_json() for _ in messages]

    assert received == messages


def test_ws_broadcasts_results_message():
    """results message with items list is forwarded intact."""
    q: asyncio.Queue = asyncio.Queue()
    msg = {
        "type": "results",
        "payload": {
            "items": [
                {"title": "BBC News", "url": "https://bbc.com", "snippet": "Breaking news"},
            ]
        },
    }
    q.put_nowait(msg)

    with patch("backend.api.websocket.message_queue", q):
        client = TestClient(_make_app(q))
        with client.websocket_connect("/ws") as ws:
            data = ws.receive_json()

    assert data["type"] == "results"
    assert data["payload"]["items"][0]["title"] == "BBC News"


def test_ws_broadcasts_tts_text_message():
    """tts_text message is forwarded intact."""
    q: asyncio.Queue = asyncio.Queue()
    msg = {"type": "tts_text", "payload": {"text": "Hello sir, how can I help you today?"}}
    q.put_nowait(msg)

    with patch("backend.api.websocket.message_queue", q):
        client = TestClient(_make_app(q))
        with client.websocket_connect("/ws") as ws:
            data = ws.receive_json()

    assert data["type"] == "tts_text"
    assert "Hello sir" in data["payload"]["text"]
