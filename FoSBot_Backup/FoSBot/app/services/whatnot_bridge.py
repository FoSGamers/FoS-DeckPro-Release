# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
import websockets
from fastapi import WebSocket
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate, ServiceControl, SettingsUpdated
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

# Global state
_STATE = {"running": False, "task": None}
_websockets: set[WebSocket] = set()

async def run_whatnot_bridge():
    """Main runner for Whatnot bridge service."""
    logger.info("Whatnot bridge runner started.")
    WS_HOST = settings.get('WS_HOST', 'localhost')
    WS_PORT = settings.get('WS_PORT', 8000)
    if not WS_HOST or not WS_PORT:
        logger.error("Missing WebSocket configuration: WS_HOST or WS_PORT not set.")
        event_bus.publish(PlatformStatusUpdate(
            platform='whatnot',
            status='disabled',
            message="Missing WebSocket host or port"
        ))
        return

    _STATE["running"] = True
    while _STATE["running"]:
        try:
            async with websockets.serve(handle_websocket, WS_HOST, WS_PORT, ping_interval=30, ping_timeout=30):
                logger.info(f"Whatnot WebSocket server running on ws://{WS_HOST}:{WS_PORT}/ws/whatnot")
                event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='connected'))
                await asyncio.Future()  # Run until cancelled
        except Exception as e:
            logger.error(f"Whatnot WebSocket server failed: {e}", exc_info=True)
            event_bus.publish(PlatformStatusUpdate(
                platform='whatnot',
                status='error',
                message=str(e)
            ))
            if _STATE["running"]:
                await asyncio.sleep(10)

async def handle_websocket(websocket: WebSocket):
    """Handles WebSocket connections for Whatnot bridge."""
    try:
        await websocket.accept()
        _websockets.add(websocket)
        logger.info("Whatnot WebSocket client connected")
        async def send_message(event: ChatMessageReceived):
            if event.message.platform == 'whatnot':
                try:
                    await websocket.send_json({
                        'type': 'chat_message',
                        'payload': {
                            'username': event.message.user,
                            'message': event.message.text,
                            'platform': event.message.platform
                        }
                    })
                    logger.debug(f"Sent Whatnot message to client: {event.message.text}")
                except Exception as e:
                    logger.error(f"Error sending message to Whatnot client: {e}")

        event_bus.subscribe(ChatMessageReceived, send_message)
        try:
            while True:
                data = await websocket.receive_json()
                logger.debug(f"Received Whatnot WebSocket message: {data}")
                if data.get('type') == 'chat_message':
                    event_bus.publish(ChatMessageReceived(
                        message=InternalChatMessage(
                            platform='whatnot',
                            channel='unknown',
                            user=data['payload']['username'],
                            text=data['payload']['message'],
                            timestamp=datetime.now().isoformat()
                        )
                    ))
                elif data.get('type') == 'queryStatus':
                    await websocket.send_json({'type': 'pong'})
                elif data.get('type') == 'debug':
                    logger.debug(f"Extension debug: {data.get('message')}")
        except websockets.exceptions.ConnectionClosed:
            logger.info("Whatnot WebSocket client disconnected")
        finally:
            event_bus.unsubscribe(ChatMessageReceived, send_message)
            _websockets.remove(websocket)
    except Exception as e:
        logger.error(f"Whatnot WebSocket handler error: {e}", exc_info=True)

async def stop_whatnot_bridge():
    """Stops the Whatnot bridge service gracefully."""
    logger.info("Stop requested for Whatnot bridge.")
    _STATE["running"] = False
    for websocket in list(_websockets):
        try:
            await websocket.close()
            _websockets.remove(websocket)
        except Exception as e:
            logger.error(f"Error closing Whatnot WebSocket: {e}")
    if _STATE.get("task") and not _STATE["task"].done():
        logger.info("Cancelling Whatnot bridge task...")
        _STATE["task"].cancel()
        try:
            await _STATE["task"]
        except asyncio.CancelledError:
            logger.info("Whatnot bridge task cancellation confirmed.")
    _STATE["task"] = None
    logger.info("Whatnot bridge stopped.")
    event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='stopped'))

async def handle_settings_update(event: SettingsUpdated):
    """Handles settings updates that affect Whatnot bridge."""
    relevant_keys = {"WS_HOST", "WS_PORT"}
    if any(key in relevant_keys for key in event.keys_updated):
        logger.info("Whatnot-relevant settings updated, requesting service restart...")
        event_bus.publish(ServiceControl(service_name="whatnot", command="restart"))

def start_whatnot_bridge_task() -> asyncio.Task | None:
    """Creates and returns a task for running the Whatnot bridge."""
    global _STATE
    if _STATE.get("task") and not _STATE["task"].done():
        logger.warning("Whatnot bridge task already running.")
        return _STATE["task"]
    logger.info("Creating background task for Whatnot bridge if WebSocket is configured.")
    if settings.get('WS_HOST') and settings.get('WS_PORT'):
        _STATE["task"] = asyncio.create_task(run_whatnot_bridge(), name="WhatnotBridgeRunner")
        event_bus.subscribe(SettingsUpdated, handle_settings_update)
        return _STATE["task"]
    else:
        logger.warning("Whatnot bridge not started due to missing WebSocket configuration.")
        event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='disabled', message="Missing WebSocket configuration"))
        return None

