# --- File: app/services/twitch_service.py --- START ---
import logging
import asyncio
import time
from twitchio.ext import commands # This import was failing initially
from twitchio import Client, Chatter, Channel, errors as twitchio_errors # Import errors
from collections import defaultdict
import datetime # Keep datetime import

# Use settings store instead of direct config import for secrets
from app.core.json_store import get_setting, load_settings
from app.core.event_bus import event_bus
from app.events import InternalChatMessage, ChatMessageReceived, BotResponseToSend, BotResponse, PlatformStatusUpdate, SettingsUpdated, ServiceControl, LogMessage

logger = logging.getLogger(__name__)

# Module level state for the service
_STATE = {
    "task": None,       # The asyncio Task running run_twitch_service
    "instance": None,   # The TwitchBot instance
    "running": False,   # Control flag for the main run loop
    "connected": False, # Actual connection status
    "settings": {}      # Cache for loaded credentials
}
# Define _run_task globally for start/stop functions
_run_task: asyncio.Task | None = None

class TwitchBot(commands.Bot):
    """Custom Twitch Bot class extending twitchio."""

    def __init__(self, token, nick, client_id, channels):
        self.initial_channels_list = [ch.strip().lower() for ch in channels if ch.strip()]
        if not self.initial_channels_list:
             logger.warning("TwitchBot initialized with no channels.")

        # Ensure token starts with oauth:
        if token and not token.startswith('oauth:'):
             token = f'oauth:{token}'

        super().__init__(
            token=token,
            client_id=client_id,
            nick=nick.lower(),
            prefix=None, # We are not using twitchio's command handling
            initial_channels=self.initial_channels_list
        )
        self._closing = False
        self._response_queue = asyncio.Queue(maxsize=100)
        self._sender_task: asyncio.Task | None = None
        logger.debug(f"TwitchBot instance created for nick '{self.nick}'.")

    async def event_ready(self):
        """Called once when the bot connects successfully."""
        global _STATE
        logger.info(f'Twitch Bot logged in as | {self.nick} ({self.user_id})')
        if self.connected_channels:
             logger.info(f'Connected to: {", ".join(ch.name for ch in self.connected_channels)}')
        else:
             logger.warning(f"Twitch Bot connected but failed to join channels: {self.initial_channels_list}.")
             # Check if initial_channels is the issue vs. channel names
             if not self.initial_channels_list:
                 logger.error("CRITICAL: No channels were provided to TwitchIO at init!")


        _STATE["connected"] = True
        self._closing = False
        event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connected'))

        if self._sender_task is None or self._sender_task.done():
             self._sender_task = asyncio.create_task(self._message_sender(), name=f"TwitchSender_{self.nick}")
             logger.info("Twitch message sender task started.")

        # Subscribe to outgoing responses ONLY when ready
        event_bus.subscribe(BotResponseToSend, self.queue_response) # Use instance method

    async def event_message(self, message):
        """Processes incoming chat messages."""
        if message.echo or self._closing or not message.author or not message.channel:
            return

        logger.debug(f"Twitch Raw: {message.raw_data}")
        logger.info(f"Twitch <{message.channel.name}> {message.author.name}: {message.content}")
        timestamp = message.timestamp.replace(tzinfo=None) if message.timestamp else datetime.datetime.utcnow()
        internal_msg = InternalChatMessage(
            platform='twitch', user=message.author.name, text=message.content, channel=message.channel.name,
            user_id=str(message.author.id), display_name=message.author.display_name, timestamp=timestamp,
            message_id=message.id, raw_data={'tags': message.tags or {}, 'is_mod': message.author.is_mod, 'is_subscriber': message.author.is_subscriber}
        )
        event_bus.publish(ChatMessageReceived(message=internal_msg))

    async def event_join(self, channel: Channel, user: Chatter):
        """Called when a user joins a channel the bot is in."""
        if user.name.lower() != self.nick: logger.debug(f"{user.name} joined #{channel.name}")

    async def event_part(self, channel: Channel, user: Chatter):
        """Called when a user leaves a channel the bot is in."""
        if user.name.lower() != self.nick: logger.debug(f"{user.name} left #{channel.name}")

    async def event_error(self, error: Exception, data: str = None):
        """Handles errors reported by the twitchio library."""
        global _STATE
        # Log less verbosely by default, provide more context
        error_name = type(error).__name__
        logger.error(f"Twitch Bot event_error received: {error_name} - {error}", exc_info=False)
        log_traceback = logger.isEnabledFor(logging.DEBUG)

        # Specific handling for authentication failures
        if isinstance(error, twitchio_errors.AuthenticationError) or 'Login authentication failed' in str(error) or 'invalid nick' in str(error).lower():
             logger.critical("Twitch login failed. Check TWITCH_TOKEN (needs 'oauth:' prefix) and TWITCH_NICK in settings.")
             event_bus.publish(PlatformStatusUpdate(platform='twitch', status='auth_error', message='Login failed - Check Credentials'))
             _STATE["running"] = False # Signal the run loop to stop retrying this config
        else:
             # Log full traceback for other unexpected errors if debugging
             if log_traceback: logger.exception(f"Full traceback for Twitch error:")
             event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message=f"{error_name}: {error}"))

    async def event_close(self):
         """Called when the bot disconnects for any reason."""
         global _STATE
         logger.warning(f"Twitch Bot connection closed (Instance: {id(self)}).")
         _STATE["connected"] = False
         if self._sender_task and not self._sender_task.done(): self._sender_task.cancel()
         if not self._closing: # Only publish if not initiated by custom_shutdown
              event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disconnected'))
              # Reconnect is handled by the run_twitch_service loop

    def queue_response(self, event: BotResponseToSend): # Use instance method (self)
         """Puts valid Twitch responses onto the sending queue."""
         global _STATE # Still need global state for connected check
         if not _STATE.get("connected") or self._closing or event.response.target_platform != 'twitch': return
         logger.debug(f"Queueing Twitch response for channel {event.response.target_channel}")
         try: self._response_queue.put_nowait(event.response)
         except asyncio.QueueFull: logger.error("Twitch response queue FULL! Discarding message.")

    async def _message_sender(self):
         """Task that pulls messages from queue and sends with rate limiting."""
         global _STATE
         SEND_DELAY = 1.6; logger.info("Twitch message sender task running.")
         while _STATE.get("connected") and not self._closing:
              try:
                   response: BotResponse = await asyncio.wait_for(self._response_queue.get(), timeout=5.0)
                   target_channel_name = response.target_channel
                   if not target_channel_name: logger.warning("Skip Twitch: no target channel."); self._response_queue.task_done(); continue
                   channel = self.get_channel(target_channel_name)
                   if not channel: logger.error(f"Cannot send Twitch: Bot not in channel '{target_channel_name}'."); self._response_queue.task_done(); continue
                   text_to_send = response.text;
                   if response.reply_to_user: clean_user = response.reply_to_user.lstrip('@'); text_to_send = f"@{clean_user}, {text_to_send}"
                   try: logger.info(f"Sending Twitch to #{target_channel_name}: {text_to_send[:100]}..."); await channel.send(text_to_send); self._response_queue.task_done(); await asyncio.sleep(SEND_DELAY)
                   except ConnectionResetError: logger.error(f"ConnectionReset sending to #{target_channel_name}."); self._response_queue.task_done(); break # Exit sender loop
                   except twitchio_errors.TwitchIOException as tio_e: logger.error(f"TwitchIO Error sending: {tio_e}"); self._response_queue.task_done(); await asyncio.sleep(SEND_DELAY)
                   except Exception as send_e: logger.error(f"Failed send to #{target_channel_name}: {send_e}", exc_info=True); self._response_queue.task_done(); await asyncio.sleep(SEND_DELAY)
              except asyncio.TimeoutError: continue # No message in queue, check running state
              except asyncio.CancelledError: logger.info("Twitch message sender task cancelled."); break
              except Exception as e: logger.exception(f"Twitch sender loop error: {e}"); await asyncio.sleep(5)
         logger.warning("Twitch message sender task stopped.")

    async def custom_shutdown(self):
         """Initiates a graceful shutdown of this bot instance."""
         global _STATE
         if self._closing: return; logger.info(f"Initiating shutdown: TwitchBot {id(self)}..."); self._closing = True; _STATE["connected"] = False; event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disconnecting'))
         if self._sender_task and not self._sender_task.done():
              if not self._sender_task.cancelling(): logger.debug("Cancelling sender task..."); self._sender_task.cancel()
              try: await self._sender_task; logger.debug("Sender task cancelled.")
              except asyncio.CancelledError: logger.debug("Sender task confirmed cancelled.")
              except Exception as e: logger.error(f"Error awaiting cancelled sender: {e}")
              self._sender_task = None
         # Clear queue BEFORE closing connection
         while not self._response_queue.empty():
             try:
                 self._response_queue.get_nowait()
                 self._response_queue.task_done()
             except asyncio.QueueEmpty: break
         logger.debug("Response queue cleared.")
         logger.debug("Closing Twitch connection...");
         try:
             await self.close()
         except Exception as e: logger.error(f"Error during twitchio bot close: {e}")
         logger.info(f"Twitch bot instance {id(self)} shutdown complete.")

# --- Service Runner & Control ---
async def run_twitch_service():
    """Main entry point to run the Twitch service with reconnection and config loading."""
    global _STATE, _run_task # Use global _run_task reference
    logger.info("Twitch service runner started.")
    while True: # Outer loop allows reloading settings
        # Check for cancellation at the start of the loop
        if _run_task and _run_task.cancelled():
             logger.info("Twitch run loop detected cancellation.")
             break

        logger.debug("Loading Twitch settings...");
        settings_data = await load_settings();
        _STATE["settings"] = settings_data
        TWITCH_TOKEN = settings_data.get("TWITCH_TOKEN");
        TWITCH_NICK = settings_data.get("TWITCH_NICK");
        TWITCH_CLIENT_ID = settings_data.get("TWITCH_CLIENT_ID");
        TWITCH_CHANNELS_RAW = settings_data.get("TWITCH_CHANNELS", "");
        TWITCH_CHANNELS = [ch.strip().lower() for ch in TWITCH_CHANNELS_RAW.split(',') if ch.strip()]

        if not all([TWITCH_TOKEN, TWITCH_NICK, TWITCH_CLIENT_ID]) or not TWITCH_CHANNELS:
            logger.warning("Twitch credentials/channels missing. Service disabled. Waiting for settings update...");
            event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disabled', message='Config missing'))
            await wait_for_settings_update({"TWITCH_TOKEN", "TWITCH_NICK", "TWITCH_CLIENT_ID", "TWITCH_CHANNELS"});
            continue # Restart outer loop

        _STATE["running"] = True; attempt = 0; MAX_ATTEMPTS=5; # Removed unused 'wait' variable
        bot_instance = None

        while _STATE.get("running") and attempt < MAX_ATTEMPTS:
            attempt += 1;
            try:
                logger.info(f"Starting Twitch bot (Attempt {attempt}/{MAX_ATTEMPTS})...");
                event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connecting'))
                bot_instance = TwitchBot(token=TWITCH_TOKEN, nick=TWITCH_NICK, client_id=TWITCH_CLIENT_ID, channels=TWITCH_CHANNELS);
                _STATE["instance"] = bot_instance
                # Bot start() runs until disconnected or closed
                await bot_instance.start()
                logger.warning("Twitch bot start() returned naturally (connection closed/lost).")
            except asyncio.CancelledError:
                logger.info("Twitch run attempt cancelled.");
                _STATE["running"] = False;
                break # Exit inner loop immediately
            except Exception as e:
                logger.error(f"Twitch connection failed (Attempt {attempt}): {e}", exc_info=logger.isEnabledFor(logging.DEBUG)) # Less verbose default
                if isinstance(e, twitchio_errors.AuthenticationError) or 'Login authentication failed' in str(e):
                    event_bus.publish(PlatformStatusUpdate(platform='twitch', status='auth_error', message="Auth Failed"))
                    logger.critical("Twitch Auth Failed. Disabling service run until settings change or restart.");
                    _STATE["running"] = False;
                    break # Stop trying with bad credentials
                else:
                    event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message=f"Connect failed: {type(e).__name__}"))
            finally:
                 # Ensure cleanup happens even if start() fails or is cancelled
                 if bot_instance:
                      logger.debug(f"Cleaning up bot instance {id(bot_instance)} after attempt {attempt}...");
                      await bot_instance.custom_shutdown()
                      _STATE["instance"] = None # Clear instance ref
                      bot_instance = None # Clear local var

            # Check running flag and max attempts BEFORE sleeping
            if not _STATE.get("running"):
                logger.info("Twitch running flag is false, exiting retry loop.");
                break
            if attempt >= MAX_ATTEMPTS:
                logger.error("Max Twitch connection attempts reached.");
                break # Exit retry loop after max attempts

            # Retry logic
            wait_time = min(attempt * 10, 60);
            logger.info(f"Waiting {wait_time}s before Twitch retry (Attempt {attempt+1})...");
            try:
                await asyncio.sleep(wait_time);
            except asyncio.CancelledError:
                logger.info("Twitch retry sleep cancelled.");
                _STATE["running"] = False;
                break # Exit inner loop

        # After inner loop finishes (naturally or by break)
        if not _STATE.get("running"):
            logger.info("Twitch service run loop detected stop signal. Exiting outer loop.");
            break # Exit the main outer loop
        elif attempt >= MAX_ATTEMPTS:
            logger.error("Max Twitch attempts reached. Waiting for settings update/restart.");
            event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message='Max attempts'));
            await wait_for_settings_update({"TWITCH_TOKEN", "TWITCH_NICK", "TWITCH_CLIENT_ID", "TWITCH_CHANNELS"})
            # Continue outer loop to reload settings

async def wait_for_settings_update(relevant_keys: set):
     """Waits for a SettingsUpdated event affecting relevant keys."""
     logger.info(f"Waiting for settings update affecting: {relevant_keys}...");
     future = asyncio.get_running_loop().create_future()
     listener_ref = None # Placeholder for the listener function itself

     async def settings_listener(event: SettingsUpdated):
          nonlocal future, listener_ref # Allow modification
          if any(key in relevant_keys for key in event.keys_updated):
               logger.info("Relevant settings updated, resuming service loop.");
               if not future.done(): future.set_result(True)
               # Attempt to unsubscribe (NOTE: Requires event bus modification or helper)
               # try: event_bus.unsubscribe(SettingsUpdated, listener_ref)
               # except ValueError: pass # Already unsubscribed or never subscribed properly
               # except AttributeError: logger.warning("EventBus does not support unsubscribe yet.")

     listener_ref = settings_listener # Store the function reference
     event_bus.subscribe(SettingsUpdated, listener_ref)
     try:
          await future # Wait until future is set by listener or cancelled
     except asyncio.CancelledError:
          logger.info("Wait for settings update cancelled.")
          # Attempt to unsubscribe on cancellation too
          # try: event_bus.unsubscribe(SettingsUpdated, listener_ref)
          # except ...
     # No finally unsubscribe here, might miss events if cancelled between check and await


async def stop_twitch_service():
     """Stops the Twitch service task gracefully."""
     global _STATE, _run_task;
     logger.info("Stop requested for Twitch service.");
     _STATE["running"] = False # Signal the run loop to stop

     bot = _STATE.get("instance")
     if bot:
          await bot.custom_shutdown() # Gracefully close connection, sender task etc.
          _STATE["instance"] = None

     current_task = _run_task;
     if current_task and not current_task.done():
         if not current_task.cancelling():
             logger.info("Cancelling Twitch run task...");
             current_task.cancel()
             try:
                 await current_task # Wait for cancellation to complete
                 logger.info("Twitch task cancellation confirmed.")
             except asyncio.CancelledError:
                 logger.info("Twitch task confirmed cancelled (exception caught).")
             except Exception as e:
                 logger.error(f"Error waiting for cancelled Twitch task: {e}")
         else:
             logger.info("Twitch task already cancelling.")
     else:
         logger.info("No active Twitch task found to cancel.")

     _run_task = None; # Clear task reference
     event_bus.publish(PlatformStatusUpdate(platform='twitch', status='stopped'))
     logger.info("Twitch service stopped.")


async def handle_settings_update(event: SettingsUpdated):
    """Restarts the Twitch service if relevant settings changed."""
    global _STATE, _run_task
    twitch_keys = {"TWITCH_TOKEN", "TWITCH_NICK", "TWITCH_CLIENT_ID", "TWITCH_CHANNELS"}
    if any(key in twitch_keys for key in event.keys_updated):
        logger.info("Relevant Twitch settings updated. Triggering restart...")
        # Publish a control event for main.py to handle restart consistently
        event_bus.publish(ServiceControl(service_name="twitch", command="restart"))


def start_twitch_service_task() -> asyncio.Task | None:
     """Creates and starts the background task for Twitch service."""
     global _run_task;
     if _run_task and not _run_task.done():
          logger.warning("Twitch service task already running or starting.")
          return _run_task

     logger.info("Creating background task for Twitch service.");
     # Subscribe to settings updates *before* starting the task
     event_bus.subscribe(SettingsUpdated, handle_settings_update);
     _run_task = asyncio.create_task(run_twitch_service(), name="TwitchServiceRunner");
     return _run_task

# --- File: app/services/twitch_service.py --- END ---