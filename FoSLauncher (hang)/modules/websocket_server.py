import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict, Optional, Set, Any
import uvicorn
import json
import sys
import threading
import time
from modules.logger.logger import FoSLogger

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("FoSLauncher")

# Create FastAPI app
logger.debug("Creating FastAPI application")
app = FastAPI()

# Add CORS middleware
logger.debug("Adding CORS middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        self.logger = FoSLogger()
        self.ws_logger = self.logger.get_logger("websocket")
        
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """Handle new WebSocket connection"""
        try:
            await websocket.accept()
            if client_id not in self.active_connections:
                self.active_connections[client_id] = set()
            self.active_connections[client_id].add(websocket)
            self.ws_logger.info(f"Client {client_id} connected")
            self.ws_logger.debug(f"Active connections: {len(self.active_connections[client_id])}")
        except Exception as e:
            self.logger.log_exception(self.ws_logger, f"Error accepting connection from {client_id}", e)
            raise

    async def disconnect(self, websocket: WebSocket, client_id: str) -> None:
        """Handle WebSocket disconnection"""
        try:
            if client_id in self.active_connections:
                self.active_connections[client_id].remove(websocket)
                self.ws_logger.info(f"Client {client_id} disconnected")
                self.ws_logger.debug(f"Remaining connections: {len(self.active_connections[client_id])}")
                if not self.active_connections[client_id]:
                    del self.active_connections[client_id]
                    self.ws_logger.debug(f"Removed client {client_id} from active connections")
        except Exception as e:
            self.logger.log_exception(self.ws_logger, f"Error handling disconnection for {client_id}", e)
            raise

    async def send_message(self, client_id: str, message: Dict[str, Any]) -> None:
        """Send message to specific client"""
        try:
            if client_id in self.active_connections:
                self.ws_logger.debug(f"Sending message to {client_id}: {message}")
                for connection in self.active_connections[client_id]:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        self.logger.log_exception(self.ws_logger, f"Error sending message to {client_id}", e)
                        await self.disconnect(connection, client_id)
            else:
                self.ws_logger.warning(f"No active connections for client {client_id}")
        except Exception as e:
            self.logger.log_exception(self.ws_logger, f"Error in send_message for {client_id}", e)
            raise

    async def broadcast(self, message: Dict[str, Any]) -> None:
        """Broadcast message to all clients"""
        try:
            self.ws_logger.debug(f"Broadcasting message: {message}")
            for client_id, connections in self.active_connections.items():
                for connection in connections:
                    try:
                        await connection.send_json(message)
                    except Exception as e:
                        self.logger.log_exception(self.ws_logger, f"Error broadcasting to {client_id}", e)
                        await self.disconnect(connection, client_id)
        except Exception as e:
            self.logger.log_exception(self.ws_logger, "Error in broadcast", e)
            raise

    def get_connection_count(self, client_id: Optional[str] = None) -> int:
        """Get number of active connections"""
        try:
            if client_id:
                return len(self.active_connections.get(client_id, set()))
            return sum(len(connections) for connections in self.active_connections.values())
        except Exception as e:
            self.logger.log_exception(self.ws_logger, "Error getting connection count", e)
            return 0

manager = WebSocketManager()

@app.on_event("startup")
async def startup_event():
    """Handle application startup"""
    manager.logger.log_info("websocket", "WebSocket server starting up")
    manager.logger.log_debug("websocket", "CORS middleware configured")

@app.on_event("shutdown")
async def shutdown_event():
    """Handle application shutdown"""
    manager.logger.log_info("websocket", "WebSocket server shutting down")
    manager.logger.log_debug("websocket", f"Active connections: {manager.get_connection_count()}")

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    """Handle WebSocket connections"""
    try:
        await manager.connect(websocket, client_id)
        manager.logger.log_info("websocket", f"New WebSocket connection established for {client_id}")
        
        try:
            while True:
                try:
                    data = await websocket.receive_json()
                    manager.logger.log_debug("websocket", f"Received message from {client_id}: {data}")
                    
                    # Process message based on type
                    message_type = data.get("type")
                    if message_type == "chat":
                        manager.logger.log_debug("websocket", f"Processing chat message from {client_id}")
                        await manager.broadcast({
                            "type": "chat",
                            "client_id": client_id,
                            "message": data.get("message", "")
                        })
                    elif message_type == "status":
                        manager.logger.log_debug("websocket", f"Processing status update from {client_id}")
                        await manager.broadcast({
                            "type": "status",
                            "client_id": client_id,
                            "status": data.get("status", "unknown")
                        })
                    else:
                        manager.logger.log_warning("websocket", f"Unknown message type from {client_id}: {message_type}")
                        
                except json.JSONDecodeError as e:
                    manager.logger.log_exception(manager.ws_logger, f"Invalid JSON from {client_id}", e)
                    await websocket.send_json({
                        "type": "error",
                        "message": "Invalid JSON format"
                    })
                except Exception as e:
                    manager.logger.log_exception(manager.ws_logger, f"Error processing message from {client_id}", e)
                    await websocket.send_json({
                        "type": "error",
                        "message": "Internal server error"
                    })
                    
        except WebSocketDisconnect:
            manager.logger.log_info("websocket", f"Client {client_id} disconnected")
        except Exception as e:
            manager.logger.log_exception(manager.ws_logger, f"Unexpected error in WebSocket connection for {client_id}", e)
        finally:
            await manager.disconnect(websocket, client_id)
            
    except Exception as e:
        manager.logger.log_exception(manager.ws_logger, f"Error in WebSocket endpoint for {client_id}", e)
        raise

if __name__ == "__main__":
    server = WebSocketServer()
    server.start() 