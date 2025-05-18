# Version History: 0.7.2 -> 0.7.3
import logging
from fastapi import WebSocket
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate, LogMessage, BotResponseToSend, BroadcastStreamerMessage
from app.core.config import logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info("Dashboard WebSocket client connected")

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info("Dashboard WebSocket client disconnected")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to dashboard client: {e}")

manager = ConnectionManager()

async def handle_chat_message(event: ChatMessageReceived):
    await manager.broadcast({
        'type': 'chat_message',
        'payload': {
            'platform': event.message.platform,
            'channel': event.message.channel,
            'user': event.message.user,
            'text': event.message.text,
            'timestamp': event.message.timestamp
        }
    })

async def handle_status_update(event: PlatformStatusUpdate):
    await manager.broadcast({
        'type': 'status_update',
        'payload': {
            'platform': event.platform,
            'status': event.status,
            'message': event.message
        }
    })

async def handle_log_message(event: LogMessage):
    await manager.broadcast({
        'type': 'log_message',
        'payload': {
            'level': event.level,
            'message': event.message
        }
    })

async def handle_bot_response(event: BotResponseToSend):
    await manager.broadcast({
        'type': 'bot_response',
        'payload': {
            'platform': event.platform,
            'channel': event.channel,
            'message': event.message
        }
    })

async def handle_broadcast_message(event: BroadcastStreamerMessage):
    await manager.broadcast({
        'type': 'streamer_message',
        'payload': {
            'platform': event.platform,
            'channel': event.channel,
            'message': event.message
        }
    })

def setup_dashboard_service_listeners():
    logger.info("Setting up dashboard service listeners...")
    event_bus.subscribe(ChatMessageReceived, handle_chat_message)
    event_bus.subscribe(PlatformStatusUpdate, handle_status_update)
    event_bus.subscribe(LogMessage, handle_log_message)
    event_bus.subscribe(BotResponseToSend, handle_bot_response)
    event_bus.subscribe(BroadcastStreamerMessage, handle_broadcast_message)

