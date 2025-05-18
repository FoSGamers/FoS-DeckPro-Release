import logging
import random
import datetime
import time # For cooldowns
from collections import defaultdict
from typing import Dict, Callable, Awaitable, Optional, Any

# Ensure core imports are correct
from app.core.config import COMMAND_PREFIX
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, CommandDetected, BotResponseToSend, BotResponse, LogMessage
# Use the generic JSON store functions
from app.core.json_store import load_json_data, save_json_data

logger = logging.getLogger(__name__)

# --- Constants for JSON filenames ---
CHECKINS_FILE = "checkins" # -> data/checkins.json
COUNTERS_FILE = "counters" # -> data/counters.json

# --- Command Handler Type ---
# Command handlers no longer need DB session for JSON version
CommandHandler = Callable[[CommandDetected], Awaitable[None]]
command_registry: Dict[str, CommandHandler] = {}

# --- Cooldowns ---
# { 'command_name': { 'user_key': last_used_timestamp } } # user_key is "platform:username"
user_cooldowns: Dict[str, Dict[str, float]] = defaultdict(dict)
# { 'command_name': last_used_timestamp }
global_cooldowns: Dict[str, float] = {}
# Cooldown durations (in seconds)
COMMAND_COOLDOWNS = {
    "default_user": 5.0,
    "default_global": 1.5, # Slightly lower default global?
    "checkin": 300.0,      # 5 min cooldown for checkin per user
    "seen": 10.0,
    "socials": 30.0,       # Limit spam for info commands
    "commands": 20.0,
    "uptime": 10.0,
    # Add specific cooldowns per command if needed
}

# Store bot start time for uptime command
start_time = datetime.datetime.utcnow()

# --- Helper to send reply ---
def send_reply(source_event: CommandDetected, text: str):
    """Creates and publishes a BotResponseToSend event."""
    # Basic validation
    if not source_event or not source_event.source_message:
        logger.error("send_reply called without valid source_event.")
        return
    msg = source_event.source_message
    if not msg.platform or not msg.user:
        logger.error(f"send_reply failed: Missing platform or user in source: {msg}")
        return

    # Construct the response object
    response = BotResponse(
        target_platform=msg.platform,
        target_channel=msg.channel, # Will be None for certain sources like admin
        text=text,
        reply_to_user=msg.user # Platform services can decide how to use this
    )
    # Publish the event for platform connectors to handle
    event_bus.publish(BotResponseToSend(response=response))
    logger.debug(f"Published BotResponseToSend to {msg.platform} channel {msg.channel} for user {msg.user}")

# --- Helper Time Delta Formatting ---
def format_timedelta_human(delta: datetime.timedelta) -> str:
    """Formats a timedelta into a human-readable string like '3d 4h' or '5m 10s'."""
    total_seconds = int(delta.total_seconds())
    secs = total_seconds # Use 'secs' alias for clarity

    if secs < 1: return "just now"

    days, remainder = divmod(secs, 86400) # 24 * 3600
    hours, remainder = divmod(remainder, 3600)
    minutes, seconds = divmod(remainder, 60) # 'seconds' now holds the final seconds part

    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    # Only show minutes if the duration is less than a day
    if minutes > 0 and days == 0:
        parts.append(f"{minutes}m")
    # Only show seconds if the duration is less than an hour (and no days)
    if seconds > 0 and days == 0 and hours == 0:
        parts.append(f"{seconds}s")

    if not parts:
        return "moments ago" # Or "0s ago" if preferred

    # Return the two most significant parts for brevity
    return " ".join(parts[:2]) + " ago"


# --- Command Handlers (Using JSON Store via helper functions) ---

async def handle_ping(event: CommandDetected):
    """Replies with a random pong variation."""
    replies = ["Pong!", "Ack!", f"Yes, {event.source_message.user}?", "I'm here!", "Present!"]
    send_reply(event, random.choice(replies))

async def handle_socials(event: CommandDetected):
    """Replies with predefined social media links."""
    # TODO: Load this text from a configuration source (e.g., settings.json via json_store)
    social_text = "Find the streamer here: Twitter - @FoS_Gamers | YouTube - /c/FoSGamers" # Example
    send_reply(event, social_text)

async def handle_lurk(event: CommandDetected):
    """Sends a thank you message for lurking."""
    send_reply(event, f"Thanks for the lurk, {event.source_message.user}! Enjoy the stream!")

async def handle_hype(event: CommandDetected):
    """Sends a hype message."""
    send_reply(event, "༼ つ ◕_◕ ༽つ HYPE! LET'S GOOOOO! ༼ つ ◕_◕ ༽つ")

async def handle_checkin(event: CommandDetected):
    """Records a user's check-in time using JSON store."""
    user = event.source_message.user
    platform = event.source_message.platform
    # Create a unique key, ensuring user_id is preferred and stringified
    user_id = str(event.source_message.user_id or user)
    checkin_key = f"{platform}:{user_id}" # Use platform:user_id as key is more robust
    now_iso = datetime.datetime.utcnow().isoformat() + "Z" # Add Z for UTC explicit

    # Load existing checkins (default to empty dict)
    checkins_data = await load_json_data(CHECKINS_FILE, default={})
    if checkins_data is None: checkins_data = {} # Ensure dict

    entry = checkins_data.get(checkin_key, {})
    entry['username'] = user # Always update username in case it changed
    entry['last_seen'] = now_iso
    if 'first_seen' not in entry:
        entry['first_seen'] = now_iso
        logger.info(f"First check-in for {user} ({user_id}) on {platform}.")
    else:
         logger.info(f"Updating check-in for {user} ({user_id}) on {platform}.")


    checkins_data[checkin_key] = entry

    # Save back to JSON
    if await save_json_data(CHECKINS_FILE, checkins_data):
        send_reply(event, f"{user} checked in!")
    else:
        send_reply(event, "Sorry, there was an error saving your check-in.")
        logger.error(f"Failed to save checkin data for {checkin_key}")

async def handle_seen(event: CommandDetected):
    """Looks up when a user was last seen checked in."""
    if not event.args:
        send_reply(event, f"Usage: {COMMAND_PREFIX}seen <username>")
        return

    target_user_lower = event.args[0].lstrip('@').lower()
    platform = event.source_message.platform
    checkin_record: Optional[Dict] = None

    checkins_data = await load_json_data(CHECKINS_FILE, default={})
    if checkins_data is None: checkins_data = {}

    # Find user case-insensitively by username (more user friendly)
    found_record = None
    found_username = None
    for key, record in checkins_data.items():
        try:
             stored_platform, _ = key.split(':', 1) # Key is platform:user_id
             stored_username = record.get('username', '')
             if stored_platform == platform and stored_username.lower() == target_user_lower:
                  found_record = record
                  found_username = stored_username # Use the correctly cased name
                  break # Found the user on this platform
        except (ValueError, TypeError): # Catch potential errors splitting key or accessing record
             logger.warning(f"Skipping invalid checkin key/record format: {key} / {record}")
        except KeyError:
             logger.warning(f"Skipping checkin record with missing username: {key}")


    if found_record and found_username:
        now = datetime.datetime.utcnow()
        try:
            # Parse ISO format string back to datetime
            # Handle potential 'Z' timezone indicator
            last_seen_str = found_record['last_seen'].rstrip('Z')
            first_seen_str = found_record['first_seen'].rstrip('Z')
            # Add timezone info if missing (assume UTC)
            last_seen_dt = datetime.datetime.fromisoformat(last_seen_str).replace(tzinfo=datetime.timezone.utc)
            first_seen_dt = datetime.datetime.fromisoformat(first_seen_str).replace(tzinfo=datetime.timezone.utc)
            # Ensure 'now' is also offset-aware for correct subtraction
            now_aware = now.replace(tzinfo=datetime.timezone.utc)

            last_seen_delta = now_aware - last_seen_dt
            first_seen_delta = now_aware - first_seen_dt
            last_seen_fmt = format_timedelta_human(last_seen_delta)
            first_seen_fmt = format_timedelta_human(first_seen_delta)
            send_reply(event, f"Found {found_username} on {platform}. First seen: {first_seen_fmt}. Last seen: {last_seen_fmt}.")
        except (ValueError, KeyError, TypeError) as e:
             logger.error(f"Error parsing stored timestamp for {found_username}: {e}", exc_info=True)
             send_reply(event, f"Sorry, couldn't read the stored time data for {event.args[0]}.")
    else:
        send_reply(event, f"Haven't seen {event.args[0]} check in on {platform} yet.")

async def handle_uptime(event: CommandDetected):
     """Reports how long the bot process has been running."""
     uptime_delta = datetime.datetime.utcnow() - start_time
     uptime_str = format_timedelta_human(uptime_delta).replace(" ago", "")
     if uptime_str == "just now": uptime_str = "a few moments"
     send_reply(event, f"Bot process uptime: {uptime_str}")

async def handle_inc_counter(event: CommandDetected):
    """Increments a counter named after the command itself (e.g., !death)."""
    counter_name = event.command # Use the command name (e.g., 'death') as the key
    counters = await load_counters() # Loads counters, ensures dict
    if counters is None: counters = {} # Safety check

    current_value = counters.get(counter_name, 0)
    new_value = current_value + 1
    counters[counter_name] = new_value

    if await save_counters(counters):
        send_reply(event, f"{counter_name.capitalize()} count increased to {new_value}!")
        logger.info(f"Counter '{counter_name}' incremented to {new_value} (JSON).")
    else:
        send_reply(event, f"Error saving counter '{counter_name}'.")
        logger.error(f"Failed to save counters data after incrementing {counter_name}")

async def handle_show_count(event: CommandDetected):
     """Shows the value of a specific counter."""
     if not event.args:
        send_reply(event, f"Usage: {COMMAND_PREFIX}showcount <counter_name>")
        return
     counter_name = event.args[0].lower()
     counters = await load_counters()
     if counters is None: counters = {}

     value = counters.get(counter_name, 0) # Default to 0 if not found
     send_reply(event, f"The current count for '{counter_name}' is: {value}")

async def handle_commands(event: CommandDetected):
    """Lists available commands."""
    # TODO: Implement permission checks later
    cmds = sorted([f"{COMMAND_PREFIX}{cmd}" for cmd in command_registry.keys()])
    reply_text = "Available commands: " + ", ".join(cmds)
    # Simple send, might need splitting for long lists later
    MAX_LEN = 480 # Leave some buffer for platform prefixes/etc.
    if len(reply_text) > MAX_LEN:
         send_reply(event, reply_text[:MAX_LEN] + "...") # Truncate for now
    else:
         send_reply(event, reply_text)


# --- Register Commands ---
def register_command(name: str, handler: CommandHandler, user_cooldown: Optional[float]=None, global_cooldown: Optional[float]=None):
    """Registers a command handler with optional cooldowns."""
    command_registry[name.lower()] = handler
    # Store cooldowns effectively
    cd_key_user = f"{name.lower()}_user"
    cd_key_global = f"{name.lower()}_global"
    if user_cooldown is not None: COMMAND_COOLDOWNS[cd_key_user] = user_cooldown
    if global_cooldown is not None: COMMAND_COOLDOWNS[cd_key_global] = global_cooldown
    logger.debug(f"Command '{name}' registered. User CD: {COMMAND_COOLDOWNS.get(cd_key_user)}, Global CD: {COMMAND_COOLDOWNS.get(cd_key_global)}")

# Register Phase 1 commands
register_command("ping", handle_ping)
register_command("socials", handle_socials, user_cooldown=30)
register_command("lurk", handle_lurk)
register_command("hype", handle_hype, user_cooldown=10, global_cooldown=3)
register_command("checkin", handle_checkin, user_cooldown=COMMAND_COOLDOWNS.get("checkin", 300))
register_command("seen", handle_seen, user_cooldown=COMMAND_COOLDOWNS.get("seen", 10))
register_command("uptime", handle_uptime, global_cooldown=5)
register_command("commands", handle_commands, user_cooldown=20)
# Register counter commands - use command name as counter key
register_command("death", handle_inc_counter)
register_command("win", handle_inc_counter)
register_command("fail", handle_inc_counter) # Example
register_command("showcount", handle_show_count)
# TODO: Add !setcounter command with permissions


# --- Main Processing Logic ---
async def process_chat_message(event: ChatMessageReceived):
    """Processes incoming chat messages from the event bus to check for commands."""
    msg = event.message
    if not msg or not msg.text or not msg.user:
        logger.debug("Ignoring empty/invalid message event.")
        return

    # Check for command prefix
    if msg.text.startswith(COMMAND_PREFIX):
        parts = msg.text.split()
        command_name = parts[0][len(COMMAND_PREFIX):].lower()
        args = parts[1:]

        # Ignore commands from Whatnot in Phase 1 for stability
        if msg.platform == 'whatnot':
            logger.debug(f"Ignoring command '{command_name}' from Whatnot user {msg.user}")
            return # Ignore Whatnot commands for now

        handler = command_registry.get(command_name)
        if handler:
            cmd_event = CommandDetected(command=command_name, args=args, source_message=msg)
            now = time.monotonic() # Use monotonic clock for reliable time differences
            is_admin = msg.platform == 'streamer_admin'
            # Use a consistent user key for cooldowns, platform:username is decent
            user_key = f"{msg.platform}:{msg.user.lower()}" # Lowercase username for consistency

            # Check Global Cooldown
            global_cd_key = command_name + "_global"
            global_cd = COMMAND_COOLDOWNS.get(global_cd_key, COMMAND_COOLDOWNS["default_global"])
            last_global_use = global_cooldowns.get(command_name, 0)
            if not is_admin and now < last_global_use + global_cd:
                remaining = (last_global_use + global_cd) - now
                logger.info(f"Cmd '{command_name}' on global CD ({remaining:.1f}s left). User: {user_key}")
                # send_reply(cmd_event, f"Command {command_name} is cooling down ({remaining:.1f}s left).") # Optional: notify user
                return # Exit

            # Check User Cooldown
            user_cd_key = command_name + "_user"
            user_cd = COMMAND_COOLDOWNS.get(user_cd_key, COMMAND_COOLDOWNS["default_user"])
            last_user_use = user_cooldowns[command_name].get(user_key, 0)
            if not is_admin and now < last_user_use + user_cd:
                 remaining = (last_user_use + user_cd) - now
                 logger.info(f"Cmd '{command_name}' on user CD for {user_key} ({remaining:.1f}s left).")
                 # send_reply(cmd_event, f"You need to wait {remaining:.1f}s to use {command_name} again.") # Optional: notify user
                 return # Exit

            # --- Cooldowns passed ---
            logger.info(f"Executing command: '{command_name}' for {user_key}")

            # Update cooldown timestamps BEFORE executing
            global_cooldowns[command_name] = now
            user_cooldowns[command_name][user_key] = now

            # Execute the handler
            try:
                # Pass only the event, no DB session needed for JSON version
                await handler(cmd_event)
            except Exception as e:
                logger.exception(f"Error executing command handler for '{command_name}': {e}")
                try: # Try sending an error reply
                    send_reply(cmd_event, f"Oops! Error running '{command_name}'.")
                except Exception: pass # Ignore reply errors

        # --- Handle Unknown Command ---
        else:
             if msg.platform != 'streamer_admin': # Don't reply to streamer's typos
                 # Create event just for replying
                 cmd_event = CommandDetected(command=command_name, args=args, source_message=msg)
                 send_reply(cmd_event, f"Unknown command: '{command_name}'. Try {COMMAND_PREFIX}commands.")


# --- Service Setup ---
def setup_chat_processor():
    """Subscribes the main message processor to the event bus."""
    event_bus.subscribe(ChatMessageReceived, process_chat_message)
    logger.info("Chat Processor (JSON Storage) setup and subscribed to messages.")