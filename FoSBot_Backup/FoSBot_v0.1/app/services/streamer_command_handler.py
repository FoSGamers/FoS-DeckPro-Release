import logging
import datetime
# Ensure config and event bus are imported correctly
from app.core.config import COMMAND_PREFIX
from app.core.event_bus import event_bus
# Ensure events are imported correctly
from app.events import StreamerInputReceived, ChatMessageReceived, BroadcastStreamerMessage, InternalChatMessage

logger = logging.getLogger(__name__)

async def handle_streamer_input(event: StreamerInputReceived):
    """Handles text input from the streamer dashboard."""
    text = event.text.strip()
    if not text:
        logger.debug("Ignoring empty streamer input.")
        return # Ignore empty input

    logger.info(f"Processing streamer input: '{text[:100]}...'") # Log truncated

    if text.startswith(COMMAND_PREFIX):
        # Treat as an admin command
        logger.info("Streamer input detected as command.")
        # Create a standard message object for the command processor
        streamer_msg = InternalChatMessage(
            platform='streamer_admin', # Special identifier
            user='STREAMER',           # Fixed admin username
            text=text,                 # The raw command string
            channel='admin_console',   # Arbitrary channel name/identifier
            timestamp=datetime.datetime.utcnow(),
            raw_data={'is_admin_command': True} # Add metadata flag
        )
        # Publish event for chat processor to handle
        # This allows admin commands to use the same logic/registry
        event_bus.publish(ChatMessageReceived(message=streamer_msg))
    else:
        # Treat as a broadcast message
        logger.info("Streamer input detected as broadcast.")
        # Publish event for platform connectors to handle
        event_bus.publish(BroadcastStreamerMessage(text=text))

def setup_streamer_command_handler():
    """Subscribes the handler to the event bus."""
    event_bus.subscribe(StreamerInputReceived, handle_streamer_input)
    logger.info("Streamer Command Handler subscribed to events.")