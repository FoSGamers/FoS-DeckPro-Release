# --- File: app/services/chat.py --- START ---
import logging
import asyncio
import datetime
import random
from app.core.event_bus import event_bus
from app.events import (
    ChatMessageReceived,
    CommandDetected,
    BotResponse,
    BotResponseToSend,
    StreamerInputReceived,
    BroadcastStreamerMessage,
)
from app.core.config import COMMAND_PREFIX
from app.core.json_store import load_checkins, save_checkins, load_commands

logger = logging.getLogger(__name__)

async def handle_chat_message(event: ChatMessageReceived):
    """Processes incoming chat messages and detects commands."""
    message = event.message
    logger.debug(f"Processing chat message from {message.platform}/{message.channel}/{message.user}: {message.text}")
    
    if message.text.startswith(COMMAND_PREFIX):
        parts = message.text[len(COMMAND_PREFIX):].strip().split()
        if parts:
            command = parts[0].lower()
            args = parts[1:]
            event_bus.publish(CommandDetected(
                command=command,
                args=args,
                source_message=message
            ))

async def handle_command(event: CommandDetected):
    """Handles detected commands and triggers appropriate responses."""
    command = event.command
    source = event.source_message
    logger.info(f"Command detected: !{command} from {source.platform}/{source.user}")
    
    response_text = None
    if command == "checkin":
        checkins = await load_checkins()
        user_key = f"{source.platform}:{source.user}"
        checkins[user_key] = {
            "last_checkin": datetime.datetime.utcnow().isoformat(),
            "platform": source.platform,
            "user": source.user,
            "channel": source.channel
        }
        await save_checkins(checkins)
        response_text = f"@{source.user} checked in successfully!"
    
    elif command == "ping":
        response_text = "Pong!"
    
    elif command == "roll":
        die = event.args[0].lower() if event.args else "d20"
        if die.startswith("d") and die[1:].isdigit():
            sides = int(die[1:])
            if sides > 0:
                result = random.randint(1, sides)
                response_text = f"@{source.user} rolled a {result} on a {die}!"
            else:
                response_text = "Invalid die: Must have at least 1 side."
        else:
            response_text = "Usage: !roll dN (e.g., !roll d20)"
    
    else:
        # Check custom commands
        commands = await load_commands()
        if command in commands:
            response_text = commands[command].replace("{user}", f"@{source.user}")
    
    if response_text:
        event_bus.publish(BotResponseToSend(
            response=BotResponse(
                platform=source.platform,
                channel=source.channel,
                text=response_text
            )
        ))

async def handle_streamer_input(event: StreamerInputReceived):
    """Handles input from the streamer via the dashboard."""
    logger.info(f"Streamer input received: {event.text}")
    if event.text.startswith(COMMAND_PREFIX):
        parts = event.text[len(COMMAND_PREFIX):].strip().split()
        if parts:
            command = parts[0].lower()
            args = parts[1:]
            event_bus.publish(CommandDetected(
                command=command,
                args=args,
                source_message=InternalChatMessage(
                    platform="dashboard",
                    channel="all",
                    user="streamer",
                    text=event.text,
                    timestamp=datetime.datetime.utcnow().isoformat()
                )
            ))
    else:
        event_bus.publish(BroadcastStreamerMessage(text=event.text))

def setup_chat_processor():
    """Sets up event listeners for chat processing."""
    logger.info("Setting up chat processor...")
    event_bus.subscribe(ChatMessageReceived, handle_chat_message)
    event_bus.subscribe(CommandDetected, handle_command)
    event_bus.subscribe(StreamerInputReceived, handle_streamer_input)
# --- File: app/services/chat.py --- END ---
