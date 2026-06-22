import sys

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from backend.state import message_queue

router = APIRouter()

# Single active connection — Jarvis is a single-user system
_active_ws: WebSocket | None = None


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """Accept one WS client and fan queue messages out to it."""
    global _active_ws
    await websocket.accept()
    _active_ws = websocket
    print("[ws] client connected", file=sys.stderr)
    try:
        while True:
            msg = await message_queue.get()
            await websocket.send_json(msg)
    except WebSocketDisconnect:
        print("[ws] client disconnected", file=sys.stderr)
    except Exception as exc:
        print(f"[ws] error: {exc}", file=sys.stderr)
    finally:
        _active_ws = None
