import logging
import json
import asyncio
from typing import List, Dict, Any, Optional # Added Optional
from fastapi import WebSocket, WebSocketDisconnect

from app.core.event_bus import event_bus
# Ensure correct import path for events
from app.events import ChatMessageReceived, StreamerInputReceived, PlatformStatusUpdate, LogMessage

logger = logging.getLogger(__name__)

class ConnectionManager:
    """Manages active WebSocket connections for the dashboard."""
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        logger.info("Dashboard Connection Manager initialized.")

    async def connect(self, websocket: WebSocket):
        """Accepts a new WebSocket connection and adds it to the list."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"Dashboard client connected: {websocket.client}")
        # Send initial status or welcome message
        try:
            await self.send_personal_message(json.dumps({"type":"status", "message":"Connected to backend!"}), websocket)
        except Exception:
             pass # Ignore if send fails immediately on connect

    def disconnect(self, websocket: WebSocket):
        """Removes a WebSocket connection from the list."""
        if websocket in self.active_connections:
            try:
                self.active_connections.remove(websocket)
                logger.info(f"Dashboard client disconnected: {websocket.client}")
            except ValueError:
                 # Already removed, ignore
                 pass

    async def send_personal_message(self, message: str, websocket: WebSocket):
        """Sends a message to a single specific WebSocket connection."""
        if websocket in self.active_connections:
            try:
                await websocket.send_text(message)
            except Exception as e:
                 # Common errors: WebSocketStateError if closed during send, ConnectionClosedOK
                 logger.warning(f"Failed to send personal message to client {websocket.client}: {e}")
                 # Disconnect on send error to clean up list
                 self.disconnect(websocket)

    async def broadcast(self, message: str):
        """Sends a message to all active WebSocket connections."""
        if not self.active_connections: return # Skip if no clients

        # Create a list of tasks to send messages concurrently
        # Iterate over a copy in case disconnect modifies the list during iteration
        tasks = [self.send_personal_message(message, connection) for connection in list(self.active_connections)]
        if tasks:
             # Wait for all send tasks to complete (or fail)
             # Using return_exceptions=True prevents one failed send from stopping others
             results = await asyncio.gather(*tasks, return_exceptions=True)
             # Log any errors that occurred during broadcast
             for result in results: # Iterate through results directly
                  if isinstance(result, Exception):
                       # Client info might be lost if disconnected, log generic error
                       logger.warning(f"Broadcast error during gather: {result}")


# Create a single instance of the manager
manager = ConnectionManager()

async def handle_dashboard_websocket(websocket: WebSocket):
    """Handles the lifecycle of a single dashboard WebSocket connection."""
    await manager.connect(websocket)
    try:
        while True:
            # Wait for a message from the client
            data = await websocket.receive_text()
            logger.debug(f"Received from dashboard client {websocket.client}: {data}")
            try:
                # Attempt to parse the message as JSON
                message_data = json.loads(data)
                msg_type = message_data.get("type")

                # Process based on message type
                if msg_type == "streamer_input":
                    text = message_data.get("text", "")
                    if text:
                        # Publish event for backend processing (delegating the work)
                        event_bus.publish(StreamerInputReceived(text=text))
                        # Optionally send confirmation back to *this* client
                        await manager.send_personal_message(json.dumps({"type": "status", "message": "Input received."}), websocket)
                    else:
                        logger.warning("Received empty streamer_input text.")
                        await manager.send_personal_message(json.dumps({"type": "error", "message": "Cannot send empty input."}), websocket)
                elif msg_type == "ping":
                    # Respond to keepalive pings from frontend
                    await manager.send_personal_message(json.dumps({"type":"pong"}), websocket)
                elif msg_type == "request_settings":
                     # Handle request from UI to get current settings
                     from app.core.json_store import load_settings # Import late to avoid potential cycles
                     settings = await load_settings()
                     # IMPORTANT: Mask secrets before sending to frontend
                     safe_settings = {}
                     for key, value in settings.items():
                          safe_settings[key] = "********" if ("TOKEN" in key or "SECRET" in key or "PASSWORD" in key) and value else value
                     await manager.send_personal_message(json.dumps({"type": "current_settings", "payload": safe_settings}), websocket)
                else:
                     logger.warning(f"Received unknown message type from dashboard: {msg_type}")
                     await manager.send_personal_message(json.dumps({"type": "error", "message": f"Unknown type: {msg_type}"}), websocket)

            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message from dashboard: {data}")
                await manager.send_personal_message(json.dumps({"type": "error", "message": "Invalid JSON format."}), websocket)
            except Exception as e:
                 logger.exception(f"Error processing message from dashboard client {websocket.client}: {e}")
                 # Send a generic error back to the client
                 try:
                      await manager.send_personal_message(json.dumps({"type": "error", "message": "Backend error processing your request."}), websocket)
                 except Exception:
                      pass # Avoid error loops if sending fails

    except WebSocketDisconnect:
        logger.info(f"Dashboard client {websocket.client} disconnected cleanly.")
    except Exception as e:
        # Handle other potential exceptions during receive_text or connection handling
        logger.error(f"Dashboard client {websocket.client} unexpected error: {e}", exc_info=True)
    finally:
        # Ensure disconnect cleanup happens regardless of how the loop exits
        manager.disconnect(websocket)


# --- Event Handlers to push info FROM the backend TO the dashboard ---
# These functions are subscribed to the event bus elsewhere (in main.py or setup)

async def push_chat_to_dashboard(event: ChatMessageReceived):
    """Formats and broadcasts chat messages to all connected dashboards."""
    if not isinstance(event, ChatMessageReceived): return # Type guard
    msg = event.message
    # Format the message clearly
    # formatted_msg = f"[{msg.platform.upper()}] {msg.user}: {msg.text}" # Frontend handles formatting now
    # Create a structured payload for the frontend JS
    payload = json.dumps({
        "type": "chat",
        "platform": msg.platform,
        "user": msg.user,
        "text": msg.text,
        "timestamp": msg.timestamp.isoformat() if msg.timestamp else None
    })
    await manager.broadcast(payload)

async def push_status_to_dashboard(event: PlatformStatusUpdate):
    """Broadcasts platform connection status updates to dashboards."""
    if not isinstance(event, PlatformStatusUpdate): return
    payload = json.dumps({
        "type": "platform_status",
        "platform": event.platform,
        "status": event.status, # e.g., 'connected', 'disconnected', 'error', 'disabled'
        "message": event.message or "" # Optional extra info
    })
    await manager.broadcast(payload)

async def push_log_to_dashboard(event: LogMessage):
    """Broadcasts important log messages (Warning/Error) to dashboards."""
    if not isinstance(event, LogMessage): return
    # Only push certain levels to avoid flooding UI
    if event.level in ["WARNING", "ERROR", "CRITICAL"]:
         payload = json.dumps({
             "type": "log",
             "level": event.level,
             "message": event.message,
             "module": event.module or "Unknown"
         })
         await manager.broadcast(payload)

# This setup function is called from main.py during startup
def setup_dashboard_service_listeners():
    """Subscribes the necessary handlers to the event bus."""
    event_bus.subscribe(ChatMessageReceived, push_chat_to_dashboard)
    event_bus.subscribe(PlatformStatusUpdate, push_status_to_dashboard)
    event_bus.subscribe(LogMessage, push_log_to_dashboard) # Display important logs
    logger.info("Dashboard Service event listeners subscribed.")