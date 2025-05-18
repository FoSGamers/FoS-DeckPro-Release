# Version History: 0.7.2 -> 0.7.3
from fastapi import WebSocket, APIRouter
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate
from app.services.dashboard_service import ConnectionManager
from app.core.config import logger
from datetime import datetime

router = APIRouter()
manager = ConnectionManager()

@router.websocket("/dashboard")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        async def send_status(event: PlatformStatusUpdate):
            await websocket.send_json({
                'type': 'status_update',
                'payload': {
                    'platform': event.platform,
                    'status': event.status,
                    'message': event.message
                }
            })

        event_bus.subscribe(PlatformStatusUpdate, send_status)
        while True:
            await websocket.receive_json()
    except Exception as e:
        logger.error(f"Dashboard WebSocket error: {e}")
    finally:
        event_bus.unsubscribe(PlatformStatusUpdate, send_status)
        await manager.disconnect(websocket)

@router.websocket("/whatnot")
async def whatnot_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        async def send_message(event: ChatMessageReceived):
            if event.message.platform == 'whatnot':
                await websocket.send_json({
                    'type': 'chat_message',
                    'payload': {
                        'username': event.message.user,
                        'message': event.message.text,
                        'platform': event.message.platform
                    }
                })

        event_bus.subscribe(ChatMessageReceived, send_message)
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
    except Exception as e:
        logger.error(f"Whatnot WebSocket error: {e}")
    finally:
        event_bus.unsubscribe(ChatMessageReceived, send_message)
        await websocket.close()

@router.websocket("/debug")
async def debug_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get('type') == 'debug':
                logger.debug(f"Extension debug: {data.get('message')}")
    except Exception as e:
        logger.error(f"Debug WebSocket error: {e}")
    finally:
        await websocket.close()

