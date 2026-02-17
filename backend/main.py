"""FastAPI application entry point."""

import logging
from fastapi import FastAPI, WebSocket
from fastapi.middleware.cors import CORSMiddleware

from ws_handler import handle_connection
from heartbeat import load_heartbeats, save_heartbeats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

app = FastAPI(title="Voice Chat Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await handle_connection(ws)


@app.get("/api/heartbeats")
async def get_heartbeats():
    return load_heartbeats()


@app.put("/api/heartbeats")
async def put_heartbeats(heartbeats: list[dict]):
    save_heartbeats(heartbeats)
    return {"status": "ok"}


@app.get("/api/health")
async def health():
    return {"status": "ok"}
