"""WebSocket connection manager for the FastAPI gateway."""
from typing import Set
from fastapi import WebSocket
from agents.ws_broadcaster import register, unregister


class ConnectionManager:
    def __init__(self):
        self.active: Set[WebSocket] = set()

    async def connect(self, ws: WebSocket) -> None:
        await ws.accept()
        self.active.add(ws)
        register(ws)

    def disconnect(self, ws: WebSocket) -> None:
        self.active.discard(ws)
        unregister(ws)


manager = ConnectionManager()
