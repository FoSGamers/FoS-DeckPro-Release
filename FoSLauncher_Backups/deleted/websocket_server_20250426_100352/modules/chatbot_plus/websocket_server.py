import logging
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import uvicorn
import json
import sys

# Configure logging with more detail
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

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

# Store active connections
logger.debug("Initializing active connections dictionary")
active_connections: Dict[str, WebSocket] = {}

@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: str):
    logger.info(f"New connection request from client {client_id}")
    await websocket.accept()
    active_connections[client_id] = websocket
    logger.info(f"Client {client_id} connected. Total clients: {len(active_connections)}")
    
    try:
        while True:
            data = await websocket.receive_text()
            logger.debug(f"Received message from {client_id}: {data}")
            
            # Broadcast message to all other clients
            for other_id, other_ws in active_connections.items():
                if other_id != client_id:
                    try:
                        logger.debug(f"Broadcasting message to client {other_id}")
                        await other_ws.send_text(data)
                    except Exception as e:
                        logger.error(f"Error sending to {other_id}: {e}")
                        
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
        active_connections.pop(client_id, None)
        logger.info(f"Remaining clients: {len(active_connections)}")
    except Exception as e:
        logger.error(f"Error in websocket connection for {client_id}: {e}")
        active_connections.pop(client_id, None)
        logger.info(f"Remaining clients: {len(active_connections)}")

async def broadcast_message(message: str):
    """Broadcast a message to all connected clients"""
    logger.debug(f"Broadcasting message to all clients: {message}")
    for client_id, websocket in active_connections.items():
        try:
            await websocket.send_text(message)
        except Exception as e:
            logger.error(f"Error broadcasting to {client_id}: {e}")

def run_server(host: str = "127.0.0.1", port: int = 8001):
    """Run the FastAPI server"""
    logger.info(f"Starting WebSocket server on {host}:{port}")
    try:
        uvicorn.run(app, host=host, port=port, log_level="debug")
    except Exception as e:
        logger.error(f"Error starting server: {e}")

if __name__ == "__main__":
    run_server() 