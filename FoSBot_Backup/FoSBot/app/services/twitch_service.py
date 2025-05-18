# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
from typing import Optional
from twitchio.ext import commands
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global state
_STATE = {"running": False, "bot": None, "task": None}

class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=settings.get('twitch_access_token', ''),
            prefix=settings.get('COMMAND_PREFIX', '!'),
            initial_channels=[ch.strip() for ch in settings.get('TWITCH_CHANNELS', '').split(',') if ch.strip()]
        )

    async def event_ready(self):
        logger.info("Twitch bot connected and ready.")
        event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connected'))

    async def event_message(self, message):
        if message.author is None:
            return
        logger.debug(f"Twitch message received: {message.author.name}: {message.content}")
        event_bus.publish(ChatMessageReceived(
            message=InternalChatMessage(
                platform='twitch',
                channel=message.channel.name,
                user=message.author.name,
                text=message.content,
                timestamp=message.timestamp.isoformat()
            )
        ))
        await self.handle_commands(message)

    @commands.command(name='ping')
    async def ping(self, ctx):
        await ctx.send('Pong!')
        logger.debug(f"Twitch ping command executed by {ctx.author.name}")

async def run_twitch_bot():
    """Main runner for Twitch bot service."""
    logger.info("Twitch bot runner started.")
    if not settings.get('twitch_access_token') or not settings.get('TWITCH_CHANNELS'):
        logger.error("Missing Twitch configuration: access token or channels not set.")
        event_bus.publish(PlatformStatusUpdate(
            platform='twitch',
            status='disabled',
            message="Missing access token or channels"
        ))
        return

    _STATE["bot"] = TwitchBot()
    _STATE["running"] = True
    while _STATE["running"]:
        try:
            await _STATE["bot"].start()
        except Exception as e:
            logger.error(f"Twitch bot failed: {e}", exc_info=True)
            event_bus.publish(PlatformStatusUpdate(
                platform='twitch',
                status='error',
                message=str(e)
            ))
            if _STATE["running"]:
                await asyncio.sleep(10)

async def stop_twitch_bot():
    """Stops the Twitch bot service gracefully."""
    logger.info("Stop requested for Twitch bot.")
    _STATE["running"] = False
    if _STATE["bot"]:
        try:
            await _STATE["bot"].close()
            logger.info("Twitch bot stopped successfully.")
        except Exception as e:
            logger.error(f"Error stopping Twitch bot: {e}")
    if _STATE.get("task") and not _STATE["task"].done():
        logger.info("Cancelling Twitch bot task...")
        _STATE["task"].cancel()
        try:
            await _STATE["task"]
        except asyncio.CancelledError:
            logger.info("Twitch bot task cancellation confirmed.")
    _STATE["task"] = None
    event_bus.publish(PlatformStatusUpdate(platform='twitch', status='stopped'))

def start_twitch_service_task() -> Optional[asyncio.Task]:
    """Creates and returns a task for running the Twitch bot."""
    global _STATE
    if _STATE.get("task") and not _STATE["task"].done():
        logger.warning("Twitch bot task already running.")
        return _STATE["task"]
    logger.info("Creating background task for Twitch service if configured.")
    if settings.get('twitch_access_token') and settings.get('TWITCH_CHANNELS'):
        _STATE["task"] = asyncio.create_task(run_twitch_bot(), name="TwitchBotRunner")
        return _STATE["task"]
    else:
        logger.warning("Twitch service not started due to missing configuration.")
        event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disabled', message="Missing configuration"))
        return None

