# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
import tweepy
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global state
_STATE = {"running": False, "task": None}

async def run_x_service():
    """Main runner for X (Twitter) service to monitor mentions."""
    logger.info("X service runner started.")
    if not all([
        settings.get('x_api_key'),
        settings.get('x_api_secret'),
        settings.get('x_access_token'),
        settings.get('x_access_token_secret')
    ]):
        logger.error("Missing X configuration: API credentials not set.")
        event_bus.publish(PlatformStatusUpdate(
            platform='x',
            status='disabled',
            message="Missing API credentials"
        ))
        return

    try:
        client = tweepy.Client(
            consumer_key=settings['x_api_key'],
            consumer_secret=settings['x_api_secret'],
            access_token=settings['x_access_token'],
            access_token_secret=settings['x_access_token_secret']
        )
        logger.debug("Tweepy client initialized")
    except Exception as e:
        logger.error(f"Failed to initialize Tweepy client: {e}")
        event_bus.publish(PlatformStatusUpdate(
            platform='x',
            status='disabled',
            message="Failed to initialize client"
        ))
        return

    _STATE["running"] = True
    since_id = None
    while _STATE["running"]:
        try:
            mentions = client.get_users_mentions(
                id=client.get_me().data.id,
                since_id=since_id,
                expansions=['author_id'],
                user_fields=['username']
            )
            if mentions.data:
                for tweet in mentions.data:
                    author = mentions.includes['users'][0].username if mentions.includes.get('users') else 'Unknown'
                    logger.debug(f"X mention received: {author}: {tweet.text}")
                    event_bus.publish(ChatMessageReceived(
                        message=InternalChatMessage(
                            platform='x',
                            channel='mentions',
                            user=author,
                            text=tweet.text,
                            timestamp=tweet.created_at.isoformat()
                        )
                    ))
                    since_id = max(since_id or 0, tweet.id)
            event_bus.publish(PlatformStatusUpdate(platform='x', status='connected'))
            await asyncio.sleep(60)  # Poll every minute
        except Exception as e:
            logger.error(f"X service error: {e}", exc_info=True)
            event_bus.publish(PlatformStatusUpdate(
                platform='x',
                status='error',
                message=str(e)
            ))
            await asyncio.sleep(10)

async def stop_x_service():
    """Stops the X service gracefully."""
    logger.info("Stop requested for X service.")
    _STATE["running"] = False
    if _STATE.get("task") and not _STATE["task"].done():
        logger.info("Cancelling X service task...")
        _STATE["task"].cancel()
        try:
            await _STATE["task"]
        except asyncio.CancelledError:
            logger.info("X service task cancellation confirmed.")
    _STATE["task"] = None
    event_bus.publish(PlatformStatusUpdate(platform='x', status='stopped'))

def start_x_service_task() -> asyncio.Task | None:
    """Creates and returns a task for running the X service."""
    global _STATE
    if _STATE.get("task") and not _STATE["task"].done():
        logger.warning("X service task already running.")
        return _STATE["task"]
    logger.info("Creating background task for X service if configured.")
    if all([
        settings.get('x_api_key'),
        settings.get('x_api_secret'),
        settings.get('x_access_token'),
        settings.get('x_access_token_secret')
    ]):
        _STATE["task"] = asyncio.create_task(run_x_service(), name="XServiceRunner")
        return _STATE["task"]
    else:
        logger.warning("X service not started due to missing configuration.")
        event_bus.publish(PlatformStatusUpdate(platform='x', status='disabled', message="Missing configuration"))
        return None

