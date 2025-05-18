# --- File: app/apis/ws_endpoints.py --- START ---
import logging
import json
import asyncio
from fastapi import APIRouter, WebSocket, WebSocketDisconnect

# --- Imports ---
# Service functions to handle the actual WebSocket logic
from app.services.dashboard_service import handle_dashboard_websocket # Corrected import during error sequence

# Event bus and related events for communication
from app.core.event_bus import event_bus
from app.events import InternalChatMessage, ChatMessageReceived

# Whatnot bridge handler (will be implemented later)
# from app.services.whatnot_bridge import handle_whatnot_websocket

# --- Setup ---
logger = logging.getLogger(__name__)
router = APIRouter()

# --- WebSocket Endpoints ---

@router.websocket("/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket):
    """
    Handles WebSocket connections from the Streamer Dashboard UI.
    Delegates handling to the dashboard_service.
    """
    await handle_dashboard_websocket(websocket)

@router.websocket("/whatnot")
async def websocket_whatnot_endpoint(websocket: WebSocket):
    """
    Handles WebSocket connections from the Whatnot Browser Extension.
    Phase 1: Receives messages, parses basic info, publishes ChatMessageReceived.
    Does not process commands originating from Whatnot or send replies back yet.
    """
    client = f"{websocket.client.host}:{websocket.client.port}" if websocket.client else "Unknown Client"
    logger.info(f"Whatnot Extension client trying connection: {client}")
    await websocket.accept()
    logger.info(f"Whatnot Extension client connected: {client}")
    try:
        while True:
            # Wait indefinitely for a message from the extension
            data = await websocket.receive_text()
            logger.debug(f"Received raw data from Whatnot Ext {client}: {data}")

            # --- CORRECTED INDENTATION & LOGIC ---
            try: # This try block likely had wrong indentation initially
                # Parse the incoming JSON data
                payload = json.loads(data)

                # Basic validation and creation of internal message object
                # Assumes extension sends {'platform': 'whatnot', 'user': '...', 'text': '...'}
                if isinstance(payload, dict) and payload.get('platform') == 'whatnot':
                    user = payload.get('user', 'WN_UnknownUser')
                    text = payload.get('text', '')
                    user_id = payload.get('user_id') # Optional user ID

                    if user and text: # Ensure minimal useful data
                        # Create standardized internal message
                        # Timestamp added automatically by InternalChatMessage dataclass default_factory
                        msg = InternalChatMessage(
                            platform='whatnot',
                            user=user,
                            text=text,
                            user_id=str(user_id) if user_id else user, # Use ID if present
                            # Add other fields if extension provides them
                            raw_data=payload # Store original payload
                        )
                        # Publish the event for other services (like dashboard) to receive
                        event_bus.publish(ChatMessageReceived(message=msg))
                    else:
                         logger.warning(f"Invalid or incomplete payload structure from Whatnot Ext {client}: Missing user or text.")
                else:
                    logger.warning(f"Invalid payload format (not dict or wrong platform) from Whatnot Ext {client}: {payload}")

            except json.JSONDecodeError:
                logger.warning(f"Received non-JSON message from Whatnot Ext {client}: {data}")
            except Exception as e:
                # Catch errors during message processing within the loop
                logger.exception(f"Error processing message from Whatnot Ext {client}: {e}")
            # --- END CORRECTION ---

    except WebSocketDisconnect as e:
        # Log disconnect code and reason if available
        logger.info(f"Whatnot Extension client {client} disconnected (Code: {e.code}, Reason: {e.reason}).")
    except Exception as e:
        # Catch other errors like connection closed unexpectedly
        logger.error(f"Unexpected error in Whatnot Extension WebSocket handler for {client}: {e}", exc_info=True)
    finally:
         # Optional cleanup if needed when a connection closes
         logger.debug(f"Closing Whatnot Extension connection handler for {client}")

# Placeholder for Whatnot Bridge Service handler if needed later
# async def handle_whatnot_websocket(websocket: WebSocket):
#     # This might be managed by a dedicated service in whatnot_bridge.py instead
#     logger.warning("Whatnot Bridge WebSocket handling not fully implemented.")
#     await websocket.accept()
#     await websocket.send_text("Whatnot Bridge Placeholder Connected")
#     await websocket.close()
# --- File: app/apis/ws_endpoints.py --- END ---