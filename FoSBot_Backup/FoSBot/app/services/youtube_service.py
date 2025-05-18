# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global state
_STATE = {"running": False, "task": None}

async def run_youtube_service():
    """Main runner for YouTube live chat service."""
    logger.info("YouTube service runner started.")
    youtube = None
    try:
        youtube = build('youtube', 'v3', developerKey=settings.get('youtube_api_key'))
        logger.debug("YouTube API client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize YouTube API client: {e}")
        event_bus.publish(PlatformStatusUpdate(
            platform='youtube',
            status='disabled',
            message="Failed to initialize API client"
        ))
        return

    _STATE["running"] = True
    while _STATE["running"]:
        try:
            # Find active live broadcast
            request = youtube.liveBroadcasts().list(
                part="id,snippet",
                broadcastStatus="active",
                maxResults=1
            )
            response = await asyncio.get_event_loop().run_in_executor(None, request.execute)
            if not response.get('items'):
                logger.warning("No active YouTube live broadcasts found.")
                event_bus.publish(PlatformStatusUpdate(
                    platform='youtube',
                    status='waiting',
                    message="No active live broadcasts"
                ))
                await asyncio.sleep(60)
                continue

            live_broadcast = response['items'][0]
            live_chat_id = live_broadcast['snippet']['liveChatId']
            logger.info(f"Found active live chat: {live_chat_id}")
            event_bus.publish(PlatformStatusUpdate(platform='youtube', status='connected'))

            # Poll live chat messages
            next_page_token = None
            while _STATE["running"]:
                request = youtube.liveChatMessages().list(
                    liveChatId=live_chat_id,
                    part="snippet,authorDetails",
                    pageToken=next_page_token
                )
                response = await asyncio.get_event_loop().run_in_executor(None, request.execute)
                for item in response.get('items', []):
                    snippet = item['snippet']
                    author = item['authorDetails']
                    event_bus.publish(ChatMessageReceived(
                        message=InternalChatMessage(
                            platform='youtube',
                            channel=author.get('channelId', 'unknown'),
                            user=author.get('displayName', 'Unknown'),
                            text=snippet.get('displayMessage', ''),
                            timestamp=snippet.get('publishedAt', '')
                        )
                    ))
                    logger.debug(f"YouTube message: {author.get('displayName')}: {snippet.get('displayMessage')}")
                next_page_token = response.get('nextPageToken')
                polling_interval = response.get('pollingIntervalMillis', 5000) / 1000
                await asyncio.sleep(polling_interval)
        except HttpError as e:
            logger.error(f"YouTube API error: {e}")
            event_bus.publish(PlatformStatusUpdate(
                platform='youtube',
                status='error',
                message=str(e)
            ))
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f"YouTube service error: {e}", exc_info=True)
            event_bus.publish(PlatformStatusUpdate(
                platform='youtube',
                status='error',
                message=str(e)
            ))
            await asyncio.sleep(10)

async def stop_youtube_service():
    """Stops the YouTube service gracefully."""
    logger.info("Stop requested for YouTube service.")
    _STATE["running"] = False
    if _STATE.get("task") and not _STATE["task"].done():
        logger.info("Cancelling YouTube service task...")
        _STATE["task"].cancel()
        try:
            await _STATE["task"]
        except asyncio.CancelledError:
            logger.info("YouTube service task cancellation confirmed.")
    _STATE["task"] = None
    event_bus.publish(PlatformStatusUpdate(platform='youtube', status='stopped'))

def start_youtube_service_task() -> asyncio.Task | None:
    """Creates and returns a task for running the YouTube service."""
    global _STATE
    if _STATE.get("task") and not _STATE["task"].done():
        logger.warning("YouTube service task already running.")
        return _STATE["task"]
    logger.info("Creating background task for YouTube service if configured.")
    if settings.get('youtube_api_key'):
        _STATE["task"] = asyncio.create_task(run_youtube_service(), name="YouTubeServiceRunner")
        return _STATE["task"]
    else:
        logger.warning("YouTube service not started due to missing API key.")
        event_bus.publish(PlatformStatusUpdate(platform='youtube', status='disabled', message="Missing API key"))
        return None

