# Version History: 0.7.2 -> 0.7.3
import time
import logging
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, CommandDetected
from app.core.config import settings

logger = logging.getLogger(__name__)

COMMAND_COOLDOWNS = {
    'ping': 5,
    'socials': 30,
    'lurk': 10,
    'hype': 15,
    'checkin': 300,
    'seen': 10,
    'uptime': 30,
    'commands': 20,
    'death': 5,
    'showcount': 5
}

_cooldowns = {}

async def handle_chat_message(event: ChatMessageReceived):
    message = event.message
    if message.platform == 'whatnot':
        return  # Ignore Whatnot for now
    content = message.text
    if not content.startswith(settings['COMMAND_PREFIX']):
        return
    command = content[len(settings['COMMAND_PREFIX']):].split()[0].lower()
    if command in COMMAND_COOLDOWNS:
        user = message.user
        now = time.time()
        if user in _cooldowns and command in _cooldowns[user]:
            if now - _cooldowns[user][command] < COMMAND_COOLDOWNS[command]:
                return
        if user not in _cooldowns:
            _cooldowns[user] = {}
        _cooldowns[user][command] = now
    event_bus.publish(CommandDetected(command=command, message=message))

def setup_chat_processor():
    logger.info("Setting up chat processor...")
    event_bus.subscribe(ChatMessageReceived, handle_chat_message)
    logger.info("Chat processor set up")

