"""
websocket_routes.py – WebSocket endpoint + connection manager. (TASK 4 hardened)

Endpoint: WS /ws/{patient_id}

Pushes realtime events:
  - dose_event
  - risk_update
  - alert_triggered

TASK 4 fixes applied:
  1. patient_id is validated BEFORE accepting the connection.
     Invalid patient → connection refused with a clear JSON error message.
  2. try/except covers ALL exceptions (not just WebSocketDisconnect) so an
     abrupt client disconnect never crashes the server.
  3. Disconnected clients are removed from _connections immediately in the
     exception handler AND in send_to_patient (for dead sockets).
"""
import asyncio
import json
import logging
from typing import Dict, List

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.utils.db_utils import fetchone

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
        logger.info(
            "WS connected: patient=%d total_connections=%d",
            patient_id,
            len(self._connections[patient_id]),
        )

    def disconnect(self, patient_id: int, ws: WebSocket) -> None:
        """Remove a websocket from the connection pool immediately."""
        conns = self._connections.get(patient_id, [])
        if ws in conns:
            conns.remove(ws)
        # Clean up the patient entry entirely when no connections remain
        if not conns:
            self._connections.pop(patient_id, None)
        logger.info("WS disconnected and removed: patient=%d", patient_id)

    async def send_to_patient(self, patient_id: int, data: dict) -> None:
        """
        Broadcast data to all active connections for this patient.
        Dead/broken sockets are detected and removed immediately.
        """
        conns = list(self._connections.get(patient_id, []))  # snapshot
        dead: List[WebSocket] = []
        for ws in conns:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        # Remove dead sockets right away
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
    """
    TASK 4 – Hardened WebSocket handler:
      • Validates patient_id BEFORE accepting the connection.
      • Catches ALL exceptions (not just WebSocketDisconnect) so an abrupt
        client disconnect never leaves the server in a bad state.
      • Removes the client from the connection pool on any exception.
    """
    # ── VALIDATION before accepting ──────────────────────────────────────────
    patient = fetchone("SELECT id FROM patients WHERE id = ?", (patient_id,))
    if patient is None:
        # Reject with 4004 close code before accepting to avoid server-side leak
        await websocket.accept()
        await websocket.send_text(json.dumps({
            "type": "error",
            "code": 4004,
            "message": f"Patient {patient_id} not found. Connection refused.",
        }))
        await websocket.close(code=4004)
        logger.warning("WS rejected: patient=%d not found", patient_id)
        return

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
        # Normal clean client disconnect
        manager.disconnect(patient_id, websocket)
        logger.info("WS clean disconnect: patient=%d", patient_id)
    except Exception as exc:
        # Abrupt disconnect, network error, or any other exception.
        # MUST remove from pool immediately to prevent memory leak / dead socket broadcast.
        manager.disconnect(patient_id, websocket)
        logger.warning("WS unexpected error for patient=%d: %s", patient_id, exc)
