from typing import Dict, Set
from fastapi import WebSocket, WebSocketDisconnect
import json
import asyncio
from datetime import datetime

from core.utils.config import get_settings


settings = get_settings()


class ConnectionManager:
    """Manages WebSocket connections for real-time updates."""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self._heartbeat_task: Dict[WebSocket, asyncio.Task] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str, building_id: str = None):
        """Accept a WebSocket connection and register it."""
        await websocket.accept()
        
        # Group connections by building_id for targeted broadcasts
        key = building_id or "global"
        if key not in self.active_connections:
            self.active_connections[key] = set()
        
        self.active_connections[key].add(websocket)
        
        # Start heartbeat
        self._heartbeat_task[websocket] = asyncio.create_task(
            self._heartbeat_loop(websocket, client_id)
        )
    
    def disconnect(self, websocket: WebSocket, building_id: str = None):
        """Remove a WebSocket connection."""
        key = building_id or "global"
        if key in self.active_connections:
            self.active_connections[key].discard(websocket)
            if not self.active_connections[key]:
                del self.active_connections[key]
        
        # Cancel heartbeat
        if websocket in self._heartbeat_task:
            self._heartbeat_task[websocket].cancel()
            del self._heartbeat_task[websocket]
    
    async def _heartbeat_loop(self, websocket: WebSocket, client_id: str):
        """Send periodic heartbeat to keep connection alive."""
        try:
            while True:
                await asyncio.sleep(settings.websocket_heartbeat_interval)
                await self.send_personal_message({
                    "type": "heartbeat",
                    "timestamp": datetime.utcnow().isoformat()
                }, websocket)
        except asyncio.CancelledError:
            pass
        except Exception:
            # Connection likely closed
            pass
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send a message to a specific connection."""
        try:
            await websocket.send_json(message)
        except Exception:
            # Connection may be closed
            pass
    
    async def broadcast_to_building(self, message: dict, building_id: str):
        """Broadcast a message to all connections for a specific building."""
        if building_id not in self.active_connections:
            return
        
        disconnected = set()
        for connection in self.active_connections[building_id]:
            try:
                await connection.send_json(message)
            except Exception:
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for conn in disconnected:
            self.disconnect(conn, building_id)
    
    async def broadcast(self, message: dict):
        """Broadcast a message to all active connections."""
        for building_id in list(self.active_connections.keys()):
            await self.broadcast_to_building(message, building_id)


# Global manager instance
manager = ConnectionManager()
