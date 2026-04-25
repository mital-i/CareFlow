"""
Shared WebSocket broadcaster used by Agent 3 and the FastAPI gateway.
Agent 3 imports broadcast() to push ActionDecision events to all dashboard clients.
"""
import asyncio
import json
from typing import Any, Dict, Set

from fastapi.websockets import WebSocket

_connections: Set[WebSocket] = set()


def register(ws: WebSocket) -> None:
    _connections.add(ws)


def unregister(ws: WebSocket) -> None:
    _connections.discard(ws)


async def broadcast(event_type: str, data: Dict[str, Any]) -> None:
    payload = json.dumps({"type": event_type, "data": data})
    dead: Set[WebSocket] = set()
    for ws in list(_connections):
        try:
            await ws.send_text(payload)
        except Exception:
            dead.add(ws)
    for ws in dead:
        _connections.discard(ws)


def broadcast_sync(event_type: str, data: Dict[str, Any]) -> None:
    """Fire-and-forget helper callable from synchronous agent handlers."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            asyncio.ensure_future(broadcast(event_type, data))
        else:
            loop.run_until_complete(broadcast(event_type, data))
    except RuntimeError:
        pass
