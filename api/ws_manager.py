"""WebSocket connection manager — shared between API and agents."""
from __future__ import annotations
import json
from typing import Any

from fastapi import WebSocket


class ConnectionManager:
    def __init__(self) -> None:
        self.active: list[WebSocket] = []

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.append(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active = [c for c in self.active if c is not ws]

    async def broadcast(self, event_type: str, data: Any) -> None:
        payload = json.dumps({"type": event_type, "data": data})
        dead = []
        for ws in self.active:
            try:
                await ws.send_text(payload)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(ws)


manager = ConnectionManager()
