from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Query
from typing import Optional
import json

from core.services.websocket_manager import manager
from core.services.timeseries_service import timeseries_service
from datetime import datetime


router = APIRouter()


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    building_id: Optional[str] = Query(None),
    client_id: Optional[str] = Query("anonymous")
):
    """WebSocket endpoint for real-time updates."""
    await manager.connect(websocket, client_id, building_id)
    
    try:
        while True:
            # Wait for client messages (for subscriptions, etc.)
            data = await websocket.receive_text()
            
            try:
                message = json.loads(data)
                message_type = message.get("type")
                
                if message_type == "subscribe":
                    # Client wants to subscribe to specific metrics
                    metrics = message.get("metrics", [])
                    building = message.get("building_id", building_id)
                    
                    # Send acknowledgment
                    await manager.send_personal_message({
                        "type": "subscribed",
                        "metrics": metrics,
                        "building_id": building
                    }, websocket)
                
                elif message_type == "ping":
                    # Respond to ping
                    await manager.send_personal_message({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }, websocket)
                    
            except json.JSONDecodeError:
                await manager.send_personal_message({
                    "type": "error",
                    "message": "Invalid JSON format"
                }, websocket)
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, building_id)
    except Exception as e:
        manager.disconnect(websocket, building_id)


@router.websocket("/ws/{building_id}")
async def building_websocket_endpoint(
    websocket: WebSocket,
    building_id: str,
    client_id: Optional[str] = Query("anonymous")
):
    """WebSocket endpoint for a specific building."""
    await websocket_endpoint(websocket, building_id, client_id)
