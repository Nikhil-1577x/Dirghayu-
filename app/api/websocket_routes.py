"""
websocket_routes.py – WebSocket endpoint + connection manager.

Endpoint: WS /ws/{patient_id}

Pushes realtime events:
  - dose_event
  - risk_update
  - alert_triggered
"""
import asyncio
import json
import logging
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)
router = APIRouter()

# ── Connection Manager ────────────────────────────────────────────────────────

class ConnectionManager:
    def __init__(self):
        # Map patient_id → list of active websocket connections
        self._connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, patient_id: int, ws: WebSocket) -> None:
        await ws.accept()
        self._connections.setdefault(patient_id, []).append(ws)
        logger.info("WS connected: patient=%d total=%d", patient_id, len(self._connections[patient_id]))

    def disconnect(self, patient_id: int, ws: WebSocket) -> None:
        conns = self._connections.get(patient_id, [])
        if ws in conns:
            conns.remove(ws)
        if not conns:
            self._connections.pop(patient_id, None)
        logger.info("WS disconnected: patient=%d", patient_id)

    async def send_to_patient(self, patient_id: int, data: dict) -> None:
        conns = self._connections.get(patient_id, [])
        dead = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(patient_id, ws)

    async def broadcast_all(self, data: dict) -> None:
        for pid in list(self._connections.keys()):
            await self.send_to_patient(pid, data)


manager = ConnectionManager()


async def broadcast(patient_id: int, data: dict) -> None:
    """Public helper called from services to push events."""
    await manager.send_to_patient(patient_id, data)


# ── WebSocket route ───────────────────────────────────────────────────────────

@router.websocket("/ws/{patient_id}")
async def websocket_endpoint(websocket: WebSocket, patient_id: int):
    await manager.connect(patient_id, websocket)
    try:
        await websocket.send_text(json.dumps({
            "type": "connected",
            "patient_id": patient_id,
            "message": f"WebSocket connected for patient {patient_id}",
        }))
        while True:
            # Keep connection alive; handle client pings
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text(json.dumps({"type": "pong"}))
    except WebSocketDisconnect:
        manager.disconnect(patient_id, websocket)
