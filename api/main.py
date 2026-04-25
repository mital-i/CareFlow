"""
CareFlow FastAPI Gateway — central HTTP/WebSocket hub.
All real-time events from Agent 3 flow through the WebSocket endpoint to the React dashboard.
"""
import os
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from api.routers import agents as agents_router
from api.routers import patients as patients_router
from api.ws_manager import manager
from vitals.api import router as vitals_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Validate dependencies on startup
    required = ["MONGODB_URI"]
    missing = [k for k in required if not os.getenv(k)]
    if missing:
        raise RuntimeError(f"Missing required env vars: {missing}")
    print("[CareFlow API] Startup checks passed")
    yield
    print("[CareFlow API] Shutting down")


app = FastAPI(
    title="CareFlow API",
    description="Autonomous Patient Monitoring & Intervention Network",
    version="0.1.0",
    lifespan=lifespan,
)

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(patients_router.router)
app.include_router(agents_router.router)
app.include_router(vitals_router)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Keep connection alive; all broadcasts are outbound from agents
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "careflow-api"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "api.main:app",
        host=os.getenv("API_HOST", "0.0.0.0"),
        port=int(os.getenv("API_PORT", "8000")),
        reload=True,
    )
