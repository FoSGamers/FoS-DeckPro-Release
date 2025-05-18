# Version History: 0.7.2 -> 0.7.3
import logging
from app.core.event_bus import event_bus
from app.events import CommandDetected, BotResponseToSend, ServiceControl
from app.core.config import logger

async def handle_streamer_command(event: CommandDetected):
    command = event.command
    message = event.message
    if command == 'ping':
        event_bus.publish(BotResponseToSend(
            platform=message.platform,
            channel=message.channel,
            message='Pong!'
        ))
    elif command in ['start', 'stop', 'restart']:
        event_bus.publish(ServiceControl(
            service_name=message.platform,
            command=command
        ))

async def handle_service_control(event: ServiceControl):
    logger.info(f"Service control command received: {event.command} for {event.service_name}")

def setup_streamer_command_handler():
    logger.info("Setting up streamer command handler...")
    event_bus.subscribe(CommandDetected, handle_streamer_command)
    event_bus.subscribe(ServiceControl, handle_service_control)

