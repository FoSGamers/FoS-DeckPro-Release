#!/bin/bash

# --- Configuration ---
PROJECT_DIR_NAME="FoSBot"
PYTHON_VERSION_TARGET="3.13"
PYTHON_VERSION_PACKAGE="python@${PYTHON_VERSION_TARGET}"
PYTHON_EXECUTABLE_NAME="python${PYTHON_VERSION_TARGET}"
DATA_DIR="data" # Directory to store JSON files
# --- End Configuration ---

# --- Safety & Setup ---
set -u; set -o pipefail
# set -e # Keep disabled for better error reporting during setup

command_exists() { command -v "$1" >/dev/null 2>&1; }
fail() { echo "" >&2; echo "ERROR: $1" >&2; exit 1; }
check_success() { CODE=$?; MSG="$1"; if [ $CODE -ne 0 ]; then fail "${MSG} (Exit code: ${CODE})"; fi; }

echo "--- FoSBot Phase 1 Setup (Webapp Config / JSON Storage) ---"
echo "---                Project: ${PROJECT_DIR_NAME}               ---"
echo ""
sleep 1

# --- Verify running location ---
CURRENT_DIR_NAME=$(basename "$PWD")
if [ "$CURRENT_DIR_NAME" != "$PROJECT_DIR_NAME" ]; then fail "Script must be run from the '$PROJECT_DIR_NAME' directory."; fi
echo "Running in: $(pwd)"

# --- [1/9] Check/Install Xcode Command Line Tools ---
echo ""; echo "[1/9] Checking/Installing Xcode Command Line Tools..."
if ! xcode-select -p > /dev/null 2>&1; then
    echo "    Initiating installation..."; echo "    >>> Please click 'Install' in the macOS dialog. <<<"; xcode-select --install
    check_success "Xcode Tools installation failed/cancelled."; echo "    Waiting for completion..."; until xcode-select -p >/dev/null 2>&1; do echo "    ..."; sleep 10; done; echo "    Xcode Tools installed."
else echo "    Xcode Tools already installed."; fi

# --- [2/9] Check/Install Homebrew ---
echo ""; echo "[2/9] Checking/Installing Homebrew..."
if ! command_exists brew; then echo "    Homebrew not found. Installing..."; /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; check_success "Homebrew install failed."; fi
if [[ -x "/opt/homebrew/bin/brew" ]]; then eval "$(/opt/homebrew/bin/brew shellenv)"; fi; if [[ -x "/usr/local/bin/brew" ]]; then eval "$(/usr/local/bin/brew shellenv)"; fi
if ! command_exists brew; then fail "Homebrew not found after install attempt."; fi
echo "    Updating Homebrew..."; brew update > /dev/null; check_success "Homebrew update failed."; echo "    Homebrew ready."

# --- [3/9] Install System Dependencies (Python, Git ONLY) ---
echo ""; echo "[3/9] Checking/Installing Python & Git via Homebrew..."
echo "    Installing/Upgrading ${PYTHON_VERSION_PACKAGE}..."; brew install ${PYTHON_VERSION_PACKAGE}; check_success "Failed to install ${PYTHON_VERSION_PACKAGE}."
echo "    Installing/Upgrading git..."; brew install git; check_success "Failed to install git."; echo "    System dependencies installed."
# Removed PostgreSQL steps

# --- [4/9] Create Project Structure ---
echo ""; echo "[4/9] Creating project structure..."
mkdir -p app/core app/services app/apis static plugins tests whatnot_extension/icons "${DATA_DIR}"
touch app/__init__.py app/core/__init__.py app/services/__init__.py app/apis/__init__.py
# No models needed yet
touch .gitignore requirements.txt README.md
touch whatnot_extension/icons/icon16.png whatnot_extension/icons/icon48.png whatnot_extension/icons/icon128.png
echo "{}" > "${DATA_DIR}/settings.json"; check_success "Failed creating settings.json"
echo "{}" > "${DATA_DIR}/checkins.json"; check_success "Failed creating checkins.json"
echo "{}" > "${DATA_DIR}/counters.json"; check_success "Failed creating counters.json"
echo "Project structure created."

# --- [5/9] Setup Python Virtual Environment ---
echo ""; echo "[5/9] Setting up Python Virtual Environment ('venv')..."
echo "    Removing old venv (if exists)..."; rm -rf venv || echo "    (No old venv/failed removal)"
echo "    Finding Python ${PYTHON_VERSION_TARGET}..."; PYTHON_PREFIX=$(brew --prefix ${PYTHON_VERSION_PACKAGE}); check_success "Could not get prefix."; PYTHON_EXECUTABLE="${PYTHON_PREFIX}/bin/${PYTHON_EXECUTABLE_NAME}"
if [ ! -x "$PYTHON_EXECUTABLE" ]; then fail "Python executable not found: ${PYTHON_EXECUTABLE}"; fi; echo "    Using: ${PYTHON_EXECUTABLE}"
echo "    Creating new venv..."; "$PYTHON_EXECUTABLE" -m venv venv; check_success "Failed to create venv."
echo "    Verifying venv structure..."; VENV_SITE_PACKAGES_PATH="venv/lib/python${PYTHON_VERSION_TARGET}/site-packages"; if [ ! -d "$VENV_SITE_PACKAGES_PATH" ]; then fail "'site-packages' MISSING."; fi; echo "    Venv created successfully."

# --- [6/9] Install Base Python Dependencies ---
echo ""; echo "[6/9] Installing base Python dependencies..."
# Define minimal requirements for server, websockets, json store, config
cat << EOF > requirements.txt
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
python-dotenv>=1.0.0
websockets>=11.0.0
aiofiles>=23.1.0
pydantic>=2.0.0
typing-extensions>=4.8.0
# Base uvicorn[standard] deps
click>=7.0
h11>=0.8
httptools>=0.5.0
pyyaml>=5.1
uvloop>=0.17.0
watchfiles>=0.13
# Other minimal needed deps
nest-asyncio>=1.5.0 # Often helpful with frameworks/async
EOF
check_success "Failed writing requirements.txt"

echo "    Activating venv..."; source venv/bin/activate; check_success "Failed activating venv."; echo "    Upgrading pip..."; ./venv/bin/pip install --upgrade pip --quiet; check_success "Pip upgrade failed."
echo "    Installing base packages..."; ./venv/bin/pip install -r requirements.txt; check_success "'pip install -r requirements.txt' failed."
echo "    Base dependencies installed."

# --- [7/9] Create Basic .env File ---
echo ""; echo "[7/9] Creating basic .env file..."
DEFAULT_WS_HOST="localhost"; DEFAULT_WS_PORT="8000"; DEFAULT_LOG_LEVEL="DEBUG"; DATA_DIR_CONFIG="${DATA_DIR}"
(
echo "# --- Application Settings ---"
echo "COMMAND_PREFIX=!"
echo "WS_HOST=${DEFAULT_WS_HOST}"
echo "WS_PORT=${DEFAULT_WS_PORT}"
echo "LOG_LEVEL=${DEFAULT_LOG_LEVEL}" # Default to DEBUG
echo "DATA_DIR=${DATA_DIR_CONFIG}"
echo ""
echo "# API Keys and Secrets are managed via the application UI (Settings Tab)"
echo "# and stored in '${DATA_DIR_CONFIG}/settings.json'"
) > .env
check_success "Failed writing .env file."
echo "    Basic .env file created."

# --- [8/9] Create Python Application Files ---
echo ""; echo "[8/9] Creating Python application source files..."

# --- app/core/config.py ---
echo "    Creating app/core/config.py..."
cat << 'EOF' > app/core/config.py
import os, logging; from dotenv import load_dotenv; from pathlib import Path
project_root = Path(__file__).parent.parent.parent; env_path = project_root / '.env'
loaded_env = load_dotenv(dotenv_path=env_path, verbose=True)
if loaded_env: print(f"Loaded .env from: {env_path}")
else: print(f"INFO: .env not found at {env_path}.")
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!"); WS_HOST = os.getenv("WS_HOST", "localhost"); WS_PORT = int(os.getenv("WS_PORT", "8000")); LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper(); DATA_DIR = Path(os.getenv("DATA_DIR", project_root / "data"))
log_level_int = getattr(logging, LOG_LEVEL, logging.INFO); logging.basicConfig(level=log_level_int, format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s', datefmt='%Y-%m-%d %H:%M:%S'); logging.getLogger("websockets").setLevel(logging.WARNING); logging.getLogger("uvicorn").setLevel(logging.INFO)
logger = logging.getLogger(__name__); logger.setLevel(log_level_int); logger.info(f"Config Loaded: WS={WS_HOST}:{WS_PORT}, Log={LOG_LEVEL}, Data='{DATA_DIR}'")
try: DATA_DIR.mkdir(parents=True, exist_ok=True); logger.info(f"Data dir verified: {DATA_DIR}")
except OSError as e: logger.error(f"CRITICAL: Cannot create data dir '{DATA_DIR}': {e}")
EOF
check_success "Failed writing app/core/config.py"

# --- app/core/json_store.py --- (With improvements)
echo "    Creating app/core/json_store.py..."
cat << 'EOF' > app/core/json_store.py
import json; import logging; import aiofiles; import asyncio; from pathlib import Path; from typing import Dict, Any, Optional, Union
from app.core.config import DATA_DIR
logger = logging.getLogger(__name__); _file_locks: Dict[Path, asyncio.Lock] = {}

async def _get_lock(filepath: Path) -> asyncio.Lock:
    """Gets or creates an asyncio Lock per file to prevent write races."""
    loop = asyncio.get_running_loop()
    if filepath not in _file_locks: _file_locks[filepath] = asyncio.Lock(loop=loop)
    return _file_locks[filepath]

async def load_json_data(filename: str, default: Any = None) -> Optional[Any]:
    filepath = DATA_DIR / f"{filename}.json"; lock = await _get_lock(filepath); logger.debug(f"Acquiring lock for read: {filepath}")
    async with lock: logger.debug(f"Lock acquired for read: {filepath}");
        try:
            if not filepath.is_file(): logger.warning(f"JSON file not found: {filepath}. Returning default."); return default
            async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f: content = await f.read()
            if not content: logger.warning(f"JSON file empty: {filepath}. Returning default."); return default
            data = json.loads(content); logger.info(f"Loaded data from {filepath}"); return data
        except json.JSONDecodeError: logger.error(f"JSON decode error in {filepath}.", exc_info=True); return default
        except Exception as e: logger.error(f"Error loading {filepath}: {e}", exc_info=True); return default
        finally: logger.debug(f"Released lock for read: {filepath}")

async def save_json_data(filename: str, data: Any) -> bool:
    filepath = DATA_DIR / f"{filename}.json"; lock = await _get_lock(filepath); temp_filepath = filepath.with_suffix(filepath.suffix + f'.{asyncio.current_task().get_name()}.tmp'); logger.debug(f"Acquiring lock for write: {filepath}")
    async with lock: logger.debug(f"Lock acquired for write: {filepath}");
        try:
            async with aiofiles.open(temp_filepath, mode='w', encoding='utf-8') as f: await f.write(json.dumps(data, indent=4, ensure_ascii=False))
            temp_filepath.rename(filepath); logger.info(f"Saved data to {filepath}"); return True
        except Exception as e: logger.error(f"Error saving {filepath}: {e}", exc_info=True);
             if temp_filepath.exists(): try: temp_filepath.unlink() except OSError: pass; return False
        finally: logger.debug(f"Released lock for write: {filepath}")

SETTINGS_FILE = "settings"; CHECKINS_FILE = "checkins"; COUNTERS_FILE = "counters"
async def load_settings() -> Dict[str, Any]: return await load_json_data(SETTINGS_FILE, default={}) or {}
async def save_settings(settings_data: Dict[str, Any]) -> bool: logger.warning("Saving settings (potentially sensitive) to plain JSON."); return await save_json_data(SETTINGS_FILE, settings_data)
async def get_setting(key: str, default: Any = None) -> Any: settings = await load_settings(); return settings.get(key, default)
async def load_checkins() -> Dict[str, Any]: return await load_json_data(CHECKINS_FILE, default={}) or {}
async def save_checkins(data: Dict[str, Any]) -> bool: return await save_json_data(CHECKINS_FILE, data)
async def load_counters() -> Dict[str, int]: return await load_json_data(COUNTERS_FILE, default={}) or {}
async def save_counters(data: Dict[str, int]) -> bool: return await save_json_data(COUNTERS_FILE, data)
EOF
check_success "Failed writing app/core/json_store.py"

# --- app/events.py ---
echo "    Creating app/events.py..."
cat << 'EOF' > app/events.py
from dataclasses import dataclass, field; from typing import Optional, Dict, Any, List; import datetime # List added
@dataclass
class InternalChatMessage: platform: str; user: str; text: str; channel: Optional[str]=None; user_id: Optional[str]=None; display_name: Optional[str]=None; timestamp: datetime.datetime=field(default_factory=datetime.datetime.utcnow); message_id: Optional[str]=None; is_command: bool=False; raw_data: Dict[str,Any]=field(default_factory=dict)
@dataclass
class BotResponse: target_platform: str; text: str; target_channel: Optional[str]=None; reply_to_user: Optional[str]=None; reply_to_message_id: Optional[str]=None
class Event: pass
@dataclass
class ChatMessageReceived(Event): message: InternalChatMessage
@dataclass
class CommandDetected(Event): command: str; args: list[str]; source_message: InternalChatMessage
@dataclass
class BotResponseToSend(Event): response: BotResponse
@dataclass
class StreamerInputReceived(Event): text: str
@dataclass
class BroadcastStreamerMessage(Event): text: str
@dataclass
class PlatformStatusUpdate(Event): platform: str; status: str; message: Optional[str]=None
@dataclass
class LogMessage(Event): level: str; message: str; module: Optional[str]=None
@dataclass
class SettingsUpdated(Event): keys_updated: List[str] # List of keys changed
@dataclass
class ServiceControl(Event): service_name: str; command: str # 'start', 'stop', 'restart'
@dataclass
class GameEvent(Event): pass # Base for game events
EOF
check_success "Failed writing app/events.py"

# --- app/core/event_bus.py --- (No changes needed)
echo "    Creating app/core/event_bus.py..."
cat << 'EOF' > app/core/event_bus.py
import asyncio, logging, sys; from collections import defaultdict; from typing import Type, Callable, Dict, List, TypeVar, Coroutine, Any; from app.events import Event
logger = logging.getLogger(__name__); T = TypeVar('T', bound=Event)
class AsyncEventBus:
    def __init__(self): self._listeners: Dict[Type[Event], List[Callable[[T], Coroutine[Any, Any, None]]]] = defaultdict(list); self._queue=asyncio.Queue(maxsize=500); self._worker_task=None; self._running=False # Added queue size
    def subscribe(self, event_type: Type[T], handler: Callable[[T], Coroutine[Any, Any, None]]):
        if not asyncio.iscoroutinefunction(handler): raise TypeError(f"Handler {handler.__name__} must be async"); self._listeners[event_type].append(handler); logger.debug(f"Handler '{getattr(handler, '__name__', repr(handler))}' subscribed to {event_type.__name__}")
    def publish(self, event: Event):
        if not self._running: logger.warning(f"Event bus not running, discarding: {type(event).__name__}"); return
        try: self._queue.put_nowait(event); logger.debug(f"Event {type(event).__name__} published.")
        except asyncio.QueueFull: logger.error(f"Event bus queue FULL! Discarding event: {type(event).__name__}. Consider increasing queue size or faster processing.")
    async def _process_events(self):
        logger.info("Event bus processor started."); while self._running:
            try: event = await self._queue.get(); event_type = type(event); logger.debug(f"Processing {event_type.__name__}")
                handlers_to_call = [];
                for reg_type, handlers in self._listeners.items():
                    if isinstance(event, reg_type): handlers_to_call.extend(handlers)
                if not handlers_to_call: self._queue.task_done(); continue
                tasks = [asyncio.create_task(handler(event), name=f"event_handler_{getattr(handler, '__name__', 'unknown')}") for handler in handlers_to_call] # Name tasks
                results = await asyncio.gather(*tasks, return_exceptions=True)
                for i, result in enumerate(results):
                    if isinstance(result, Exception): hn = getattr(handlers_to_call[i], '__name__', repr(handlers_to_call[i])); logger.error(f"Exception in handler '{hn}' for {event_type.__name__}: {result}", exc_info=result if logger.isEnabledFor(logging.DEBUG) else False)
                self._queue.task_done()
            except asyncio.CancelledError: logger.info("Event processor cancelled."); break
            except Exception as e: logger.exception(f"Event processor error: {e}"); await asyncio.sleep(1)
        logger.info("Event bus processor stopped.")
    async def start(self):
        if self._running: logger.warning("Event bus already running."); return
        self._running=True; self._worker_task=asyncio.create_task(self._process_events(), name="EventBusProcessor"); logger.info("Event bus started.")
    async def stop(self):
        if not self._running or not self._worker_task or self._worker_task.done(): logger.info("Event bus already stopped."); return
        logger.info("Stopping event bus..."); self._running=False; # Signal loop to stop
        # Add small item to queue to unblock worker if waiting on empty queue
        try: self._queue.put_nowait(None) # Sentinel value, processor needs to handle None gracefully or just exit
        except asyncio.QueueFull: pass # Ignore if full during shutdown
        if not self._worker_task.done(): self._worker_task.cancel() # Cancel task
        try: await self._worker_task; logger.info("Event bus stopped.")
        except asyncio.CancelledError: logger.info("Event bus stop confirmed (cancelled).")
        except Exception as e: logger.exception(f"Error during event bus shutdown: {e}")
        finally: self._worker_task = None
event_bus = AsyncEventBus()
EOF
check_success "Failed writing app/core/event_bus.py"

# --- Service Stubs/Placeholders ---
echo "    Creating service stubs (twitch, youtube, x, whatnot)..."
cat << 'EOF' > app/services/twitch_service.py
import logging; logger=logging.getLogger(__name__); import asyncio; from app.core.event_bus import event_bus; from app.events import PlatformStatusUpdate, SettingsUpdated, BotResponseToSend; from app.core.json_store import get_setting, load_settings
_STATE = {"task": None, "instance": None, "running": False, "settings": {}} # Module level state
async def run_twitch_service(): # The main loop
    global _STATE; logger.info("Twitch run loop started."); _STATE["running"] = True
    while _STATE["running"]:
        token = _STATE["settings"].get("TWITCH_TOKEN"); nick = _STATE["settings"].get("TWITCH_NICK"); client_id = _STATE["settings"].get("TWITCH_CLIENT_ID"); channels_raw = _STATE["settings"].get("TWITCH_CHANNELS",""); channels = [c.strip().lower() for c in channels_raw.split(',') if c.strip()]
        if not all([token, nick, client_id]) or not channels: logger.warning("Twitch config missing in settings.json. Stopping."); event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disabled', message='Config missing')); _STATE["running"]=False; break
        bot = None; attempt = 0; MAX_ATTEMPTS=5; wait = 5
        while _STATE["running"] and attempt < MAX_ATTEMPTS:
            attempt += 1; logger.info(f"Attempting Twitch connection (Attempt {attempt}/{MAX_ATTEMPTS})..."); event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connecting'))
            try: from twitchio.ext import commands; bot = commands.Bot(token=token, client_id=client_id, nick=nick, prefix=None, initial_channels=channels); _STATE["instance"] = bot # Store instance
                 # Simplified event handlers inline for this stub
                 @bot.event async def event_ready(): logger.info(f"Twitch Bot Ready as {bot.nick}"); event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connected')); event_bus.subscribe(BotResponseToSend, handle_send_response) # Subscribe here
                 @bot.event async def event_message(message):
                     if message.echo or not message.author: return; from app.events import InternalChatMessage, ChatMessageReceived; import datetime; ts = message.timestamp.replace(tzinfo=None) if message.timestamp else datetime.datetime.utcnow(); msg=InternalChatMessage(platform='twitch', user=message.author.name, text=message.content, channel=message.channel.name, user_id=str(message.author.id), display_name=message.author.display_name, timestamp=ts, message_id=message.id, raw_data={'tags': message.tags or {}}); event_bus.publish(ChatMessageReceived(message=msg))
                 @bot.event async def event_close(): logger.warning("Twitch connection closed by server."); event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disconnected')) # Let outer loop handle reconnect
                 @bot.event async def event_error(error, data=None): logger.error(f"Twitch Error: {error}"); event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message=str(error))); if 'authentication failed' in str(error): raise error # Raise auth errors to stop retries
                 await bot.start(); logger.info("Twitch bot start() returned (connection closed).") # If it returns, connection closed
            except asyncio.CancelledError: logger.info("Twitch run cancelled."); _STATE["running"]=False; break # Exit outer loop too
            except Exception as e: logger.error(f"Twitch connection failed (Attempt {attempt}): {e}"); event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message=f"Connect attempt failed: {e}")); if 'authentication failed' in str(e): logger.critical("Twitch Auth failed. Stopping."); _STATE["running"]=False; break # Stop retries on auth error
            finally: if bot: await bot.close(); _STATE["instance"]=None # Ensure close
            if not _STATE["running"]: break # Exit if stop was requested during attempt
            logger.info(f"Waiting {wait}s before Twitch retry..."); await asyncio.sleep(wait); wait = min(wait * 2, 60) # Exponential backoff
        if not _STATE["running"]: logger.info("Twitch service run loop exiting."); break # Break outer loop if stopped
        if attempt >= MAX_ATTEMPTS: logger.error("Max Twitch connection attempts reached. Stopping service."); _STATE["running"]=False; event_bus.publish(PlatformStatusUpdate(platform='twitch', status='error', message='Max connection attempts')); break
async def handle_send_response(event: BotResponseToSend): # Standalone response handler
    global _STATE; bot = _STATE.get("instance"); if not bot or not bot.is_connected or event.response.target_platform != 'twitch': return
    resp=event.response; chan_name=resp.target_channel; text=resp.text; if not chan_name: return
    chan = bot.get_channel(chan_name); if not chan: logger.warning(f"Twitch chan '{chan_name}' not found."); return
    if resp.reply_to_user: text = f"@{resp.reply_to_user.lstrip('@')}, {text}"
    try: logger.info(f"Sending Twitch to #{chan_name}: {text[:50]}..."); await chan.send(text)
    except Exception as e: logger.error(f"Failed Twitch send to #{chan_name}: {e}")
async def handle_settings_update(event: SettingsUpdated):
    global _STATE; twitch_keys={"TWITCH_TOKEN","TWITCH_NICK","TWITCH_CLIENT_ID","TWITCH_CHANNELS"};
    if any(k in twitch_keys for k in event.keys_updated): logger.info("Twitch settings updated, triggering restart..."); await stop_twitch_service(); await asyncio.sleep(1); start_twitch_service_task() # Trigger full restart via task helper
async def stop_twitch_service():
    global _STATE, _run_task; logger.info("Stopping Twitch service..."); _STATE["running"] = False; bot = _STATE.get("instance")
    # Unsubscribe - needs unsubscribe method on event bus
    # try: event_bus.unsubscribe(BotResponseToSend, handle_send_response) except: pass
    if bot: logger.info("Closing Twitch bot instance..."); await bot.close(); _STATE["instance"] = None
    if _run_task and not _run_task.done(): logger.info("Cancelling Twitch run task..."); _run_task.cancel();
        try: await _run_task; logger.info("Twitch task cancelled.")
        except asyncio.CancelledError: logger.info("Twitch task confirmed cancelled.")
        except Exception as e: logger.error(f"Error waiting for cancelled Twitch task: {e}")
    _run_task = None; logger.info("Twitch service stopped.")
def start_twitch_service_task():
    global _run_task, _STATE;
    if _run_task and not _run_task.done(): logger.warning("Twitch task already running."); return _run_task
    logger.info("Creating background task for Twitch service."); event_bus.subscribe(SettingsUpdated, handle_settings_update); _run_task = asyncio.create_task(run_twitch_service(), name="TwitchRunner"); return _run_task
EOF
check_success "Failed writing app/services/twitch_service.py"
echo "    Creating app/services/youtube_service.py (stub)..."
cat << 'EOF' > app/services/youtube_service.py
import logging; logger=logging.getLogger(__name__); import asyncio; from app.core.event_bus import event_bus; from app.events import PlatformStatusUpdate
async def run_youtube_service(): event_bus.publish(PlatformStatusUpdate(platform='youtube', status='disabled', message='Not implemented')); logger.warning("YouTube service NOT IMPLEMENTED."); await asyncio.sleep(3600*24) # Sleep long time
async def stop_youtube_service(): logger.info("YouTube service stop called (stub).")
def start_youtube_service_task(): logger.info("YouTube service start called (stub)."); return None # Return None as no task created
EOF
echo "    Creating app/services/x_service.py (stub)..."
cat << 'EOF' > app/services/x_service.py
import logging; logger=logging.getLogger(__name__); import asyncio; from app.core.event_bus import event_bus; from app.events import PlatformStatusUpdate
async def run_x_service(): event_bus.publish(PlatformStatusUpdate(platform='x', status='disabled', message='Not implemented')); logger.warning("X/Twitter service NOT IMPLEMENTED."); await asyncio.sleep(3600*24)
async def stop_x_service(): logger.info("X/Twitter service stop called (stub).")
def start_x_service_task(): logger.info("X/Twitter service start called (stub)."); return None
EOF
echo "    Creating app/services/whatnot_bridge.py (stub)..."
cat << 'EOF' > app/services/whatnot_bridge.py
import logging; logger=logging.getLogger(__name__); import asyncio; from app.core.event_bus import event_bus; from app.events import PlatformStatusUpdate
# This service would likely manage the pool of WS connections from the extension
# For now, it's just a placeholder task
async def run_whatnot_bridge(): event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='disabled', message='Bridge not active')); logger.warning("Whatnot Bridge service NOT IMPLEMENTED."); await asyncio.sleep(3600*24)
async def stop_whatnot_bridge(): logger.info("Whatnot Bridge stop called (stub).")
def start_whatnot_bridge_task(): logger.info("Whatnot Bridge start called (stub)."); return None
EOF
check_success "Failed writing service stubs"

# --- app/apis/ws_endpoints.py ---
echo "    Creating app/apis/ws_endpoints.py..."
# ... (cat EOF > app/apis/ws_endpoints.py ... same as before) ...
cat << 'EOF' > app/apis/ws_endpoints.py
import logging; import json; from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.dashboard_service import handle_dashboard_websocket
from app.core.event_bus import event_bus; from app.events import InternalChatMessage
logger = logging.getLogger(__name__); router = APIRouter()
@router.websocket("/dashboard")
async def websocket_dashboard_endpoint(websocket: WebSocket): await handle_dashboard_websocket(websocket)
@router.websocket("/whatnot")
async def websocket_whatnot_endpoint(websocket: WebSocket):
    client = f"{websocket.client.host}:{websocket.client.port}"; logger.info(f"Whatnot Ext client connected: {client}"); await websocket.accept()
    try:
        while True: data = await websocket.receive_text(); logger.debug(f"From Whatnot Ext {client}: {data}")
            try: # Parse and publish ONLY, no command processing here
                 payload = json.loads(data)
                 if 'platform' in payload and payload['platform'] == 'whatnot': # Basic validation
                      msg = InternalChatMessage(platform='whatnot', user=payload.get('user','WN_User'), text=payload.get('text',''), raw_data=payload)
                      event_bus.publish(ChatMessageReceived(message=msg))
                 else: logger.warning(f"Invalid payload from Whatnot Ext: {data}")
            except json.JSONDecodeError: logger.warning(f"Non-JSON from Whatnot Ext: {data}")
            except Exception as e: logger.exception(f"Error processing msg from Whatnot Ext: {e}")
    except WebSocketDisconnect: logger.info(f"Whatnot Ext client {client} disconnected.")
    except Exception as e: logger.error(f"Whatnot Ext WS error for {client}: {e}", exc_info=True)
    finally: logger.debug(f"Closing Whatnot Ext WS handler for {client}")
EOF
check_success "Failed writing app/apis/ws_endpoints.py"

# --- app/apis/settings_api.py --- (Updated for clarity)
echo "    Creating app/apis/settings_api.py..."
cat << 'EOF' > app/apis/settings_api.py
import logging; from fastapi import APIRouter, HTTPException, Body; from pydantic import BaseModel, Field; from typing import Dict, Any, List, Optional
from app.core.json_store import load_settings, save_settings; from app.core.event_bus import event_bus; from app.events import SettingsUpdated, ServiceControl
logger = logging.getLogger(__name__); router = APIRouter()

class AllSettings(BaseModel): # Use one model for easier updates
    TWITCH_TOKEN: Optional[str] = None; TWITCH_CLIENT_ID: Optional[str] = None; TWITCH_NICK: Optional[str] = None; TWITCH_CHANNELS: Optional[str] = None
    YOUTUBE_API_KEY: Optional[str] = None; YOUTUBE_CLIENT_SECRETS_FILE: Optional[str] = None; YOUTUBE_LIVE_CHAT_ID: Optional[str] = None
    X_BEARER_TOKEN: Optional[str] = None; X_API_KEY: Optional[str] = None; X_API_SECRET: Optional[str] = None; X_ACCESS_TOKEN: Optional[str] = None; X_ACCESS_SECRET: Optional[str] = None; X_HASHTAG_OR_MENTION: Optional[str] = None
    # Add non-secret app settings if needed: COMMAND_PREFIX: Optional[str] = None etc.

@router.get("/settings", response_model=Dict[str, Any], summary="Get Current Settings (Secrets Masked)")
async def get_current_settings():
    settings = await load_settings(); safe_settings = {};
    for key, value in settings.items(): safe_settings[key] = "********" if ("TOKEN" in key or "SECRET" in key or "PASSWORD" in key) and value else value
    return safe_settings

@router.post("/settings", status_code=200, summary="Update Settings")
async def update_settings_endpoint(new_settings: AllSettings = Body(...)):
    logger.info("Received POST /api/settings"); current_settings = await load_settings(); updated_keys = []; update_data = new_settings.dict(exclude_unset=True)
    if not update_data: raise HTTPException(status_code=400, detail="No settings provided.")
    for key, value in update_data.items():
        # Update if value is provided (not None) AND is different from current or key doesn't exist
        # Treat empty string "" as a valid value to set (e.g., clearing optional field)
        if value is not None and current_settings.get(key) != value:
            current_settings[key] = value; updated_keys.append(key); logger.debug(f"Setting '{key}' updated.")
    if not updated_keys: logger.info("No actual changes to settings."); return {"message": "No settings changed."}
    if await save_settings(current_settings): logger.info(f"Settings updated for keys: {updated_keys}"); event_bus.publish(SettingsUpdated(keys_updated=updated_keys)); return {"message": f"Settings updated successfully ({', '.join(updated_keys)}). Service restart may be needed."}
    else: raise HTTPException(status_code=500, detail="Failed to save settings.")

@router.post("/control/{service_name}/{command}", status_code=200, summary="Control Services (start/stop/restart)")
async def control_service(service_name: str, command: str):
     allowed_services = ["twitch", "youtube", "x", "whatnot"]; allowed_commands = ["start", "stop", "restart"]; service_name = service_name.lower(); command = command.lower()
     if service_name not in allowed_services: raise HTTPException(status_code=404, detail="Service not found.")
     if command not in allowed_commands: raise HTTPException(status_code=400, detail="Invalid command.")
     logger.info(f"Control command '{command}' for service '{service_name}' received."); event_bus.publish(ServiceControl(service_name=service_name, command=command)); return {"message": f"'{command}' command sent to '{service_name}' service."}

EOF
check_success "Failed writing app/apis/settings_api.py"

# --- app/main.py --- (Final version - slightly updated)
echo "    Creating app/main.py..."
# Paste the full corrected main.py (with JSON focus) from previous response here
cat << 'EOF' > app/main.py
import asyncio; import logging; import signal; from fastapi import FastAPI; from fastapi.staticfiles import StaticFiles; from contextlib import asynccontextmanager; from pathlib import Path; import sys
from app.core.config import logger; from app.core.event_bus import event_bus
from app.apis import ws_endpoints, settings_api # Import settings_api
from app.services.twitch_service import start_twitch_service_task, stop_twitch_service
from app.services.youtube_service import start_youtube_service_task, stop_youtube_service
from app.services.x_service import start_x_service_task, stop_x_service
from app.services.whatnot_bridge import start_whatnot_bridge_task, stop_whatnot_bridge
from app.services.chat_processor import setup_chat_processor
from app.services.dashboard_service import setup_dashboard_service_listeners
from app.services.streamer_command_handler import setup_streamer_command_handler
from app.events import ServiceControl

background_tasks = set(); _service_tasks_map: dict[str, asyncio.Task | None] = {} # Store running tasks

async def handle_service_control(event: ServiceControl):
     logger.info(f"Handling control: '{event.command}' for '{event.service_name}'"); control_funcs = service_control_map.get(event.service_name); task = _service_tasks_map.get(event.service_name)
     if not control_funcs: logger.error(f"No controls for '{event.service_name}'"); return
     start_func=control_funcs.get("start"); stop_func=control_funcs.get("stop");
     if event.command == "stop":
          if stop_func: await stop_func()
          else: logger.warning(f"No stop func for '{event.service_name}'")
          _service_tasks_map[event.service_name] = None # Clear task reference
     elif event.command == "start":
          if task and not task.done(): logger.warning(f"Service '{event.service_name}' already running/starting."); return
          if start_func: new_task = start_func();
               if new_task: _service_tasks_map[event.service_name] = new_task; background_tasks.add(new_task); new_task.add_done_callback(background_tasks.discard)
          else: logger.warning(f"No start func for '{event.service_name}'")
     elif event.command == "restart":
          logger.info(f"Restarting '{event.service_name}'...");
          if stop_func: await stop_func(); await asyncio.sleep(1)
          else: logger.warning(f"No stop func for restart of '{event.service_name}'")
          if start_func: new_task = start_func();
               if new_task: _service_tasks_map[event.service_name] = new_task; background_tasks.add(new_task); new_task.add_done_callback(background_tasks.discard)
          else: logger.warning(f"No start func for restart of '{event.service_name}'")

service_control_map = { "twitch": {"start": start_twitch_service_task, "stop": stop_twitch_service}, "youtube": {"start": start_youtube_service_task, "stop": stop_youtube_service}, "x": {"start": start_x_service_task, "stop": stop_x_service}, "whatnot": {"start": start_whatnot_bridge_task, "stop": stop_whatnot_bridge} }

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("--- Application startup sequence ---"); logger.info("Starting event bus..."); await event_bus.start()
    logger.info("Setting up listeners..."); setup_chat_processor(); setup_dashboard_service_listeners(); setup_streamer_command_handler(); event_bus.subscribe(ServiceControl, handle_service_control)
    logger.info("Startup listeners complete. Services will start based on saved settings via UI/API trigger."); logger.info("--- Application startup complete. Running! ---")
    yield # App runs
    logger.info("--- Application shutdown sequence ---"); logger.info("Stopping platform services...");
    await asyncio.gather(stop_twitch_service(), stop_youtube_service(), stop_x_service(), stop_whatnot_bridge(), return_exceptions=True) # Stop all in parallel
    logger.info("Waiting briefly..."); await asyncio.sleep(1); logger.info("Stopping event bus..."); await event_bus.stop()
    if background_tasks: logger.warning(f"Cancelling {len(background_tasks)} lingering tasks...");
    for task in list(background_tasks):
         if task and not task.done(): task.cancel()
    if background_tasks: try: await asyncio.wait_for(asyncio.gather(*background_tasks, return_exceptions=True), timeout=5.0); except Exception: pass
    logger.info("--- Application shutdown complete. ---")

app = FastAPI(title="FoSBot (JSON Config)", version="0.3.0-json", lifespan=lifespan); app.include_router(ws_endpoints.router, prefix="/ws"); app.include_router(settings_api.router, prefix="/api", tags=["Settings & Control"])
STATIC_DIR = "static";
if not Path(STATIC_DIR).is_dir(): logger.error(f"Static dir '{STATIC_DIR}' not found!")
else: try: app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static"); logger.info(f"Mounted static files from './{STATIC_DIR}'.")
      except Exception as e: logger.exception(f"Failed mount static: {e}")
if __name__ == "__main__": import uvicorn; from app.core.config import WS_HOST, WS_PORT, LOG_LEVEL; logger.warning("Run via 'uvicorn app.main:app --reload'."); uvicorn.run("app.main:app", host=WS_HOST, port=WS_PORT, log_level=LOG_LEVEL.lower(), reload=False)

EOF
check_success "Failed writing app/main.py"

echo "    Python application files created."

# --- [9/10] Create Whatnot Extension Files ---
echo ""; echo "[9/10] Setting up Whatnot Extension files..."
# ... (manifest, background, popup.html, popup.js, content.js - use final versions from previous answers) ...
# (Ensure content.js includes inspector logic)
cat << 'EOF' > whatnot_extension/manifest.json
{"manifest_version": 3,"name": "FoSBot Whatnot Helper","version": "0.3.0","description": "Reads Whatnot chat. Requires config via popup.","permissions": ["storage","activeTab","scripting"],"host_permissions": ["*://*.whatnot.com/*"],"background": {"service_worker": "background.js"},"content_scripts": [{"matches": ["*://*.whatnot.com/*"],"js": ["content.js"],"run_at": "document_idle","all_frames": false}],"action": {"default_popup": "popup.html","default_icon": {"16": "icons/icon16.png","48": "icons/icon48.png","128": "icons/icon128.png"}},"icons": {"16": "icons/icon16.png","48": "icons/icon48.png","128": "icons/icon128.png"}}
EOF
cat << 'EOF' > whatnot_extension/background.js
chrome.runtime.onInstalled.addListener(details => { console.log(`FoSBot WN Helper ${details.reason}.`); }); console.log("FoSBot BG Loaded.");
EOF
cat << 'EOF' > whatnot_extension/popup.html
<!DOCTYPE html><html><head><title>FoSBot Helper</title><meta charset="UTF-8"><style>body{width:250px;font-family:sans-serif;padding:10px;font-size:14px}button{margin-top:10px;padding:5px 10px;cursor:pointer}p{margin:5px 0;line-height:1.3}#status,#ws-status{font-style:italic;color:grey;min-height:1.2em;margin-top:5px}#currentSelectors{margin-top:15px;font-size:11px;color:#333;max-height:150px;overflow-y:auto;border-top:1px solid #ccc;padding-top:5px;background-color:#f9f9f9;padding:5px;border-radius:3px}#currentSelectors div{white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin-bottom:3px}strong{display:block;margin-bottom:4px}</style></head><body><h3>Whatnot Selectors</h3><p>Configure elements for chat interaction. Click, then follow overlay prompts.</p><button id="configureButton">Configure/Re-Configure</button><div id="status"></div><div id="ws-status">WS: Loading...</div><div id="currentSelectors">Loading...</div><script src="popup.js"></script></body></html>
EOF
cat << 'EOF' > whatnot_extension/popup.js
const cfgBtn=document.getElementById('configureButton');const statEl=document.getElementById('status');const selDiv=document.getElementById('currentSelectors');const wsStatEl=document.getElementById('ws-status');
function displaySelectors(){chrome.storage.local.get(['whatnotSelectors'],(r)=>{selDiv.innerHTML='<strong>Current:</strong><br>';if(r.whatnotSelectors){const k=['chatContainer','messageItem','username','messageText','chatInput','sendButton'];k.forEach(key=>{const d=document.createElement('div');const v=r.whatnotSelectors[key];d.textContent=`${key}: ${v||'N/A'}`;d.title=v||'N/A';selDiv.appendChild(d);});}else{selDiv.innerHTML+='<i>None saved.</i>';}});}
function checkConnection(){wsStatEl.textContent='WS: Chk...';chrome.tabs.query({active:true,currentWindow:true},(tabs)=>{const wt=tabs.find(t=>t.url&&t.url.includes('whatnot.com'));if(wt&&wt.id){chrome.tabs.sendMessage(wt.id,{action:"query_status"},(r)=>{if(chrome.runtime.lastError){wsStatEl.textContent=`WS: Err`;console.error(chrome.runtime.lastError.message);}else if(r){wsStatEl.textContent=`WS: ${r.ws_status||'?'}`;if(r.selectors_ok===false)statEl.textContent="WARN: Selectors missing!";else if(r.selectors_ok===true)statEl.textContent="Selectors loaded.";}else{wsStatEl.textContent='WS: No Resp';}});}});}
cfgBtn.addEventListener('click',()=>{statEl.textContent='Sending...';chrome.tabs.query({active:true,currentWindow:true},(tabs)=>{const wt=tabs.find(t=>t.url&&t.url.includes('whatnot.com'));if(wt&&wt.id){chrome.tabs.sendMessage(wt.id,{action:"start_inspector"},(r)=>{if(chrome.runtime.lastError){statEl.textContent=`Err: ${chrome.runtime.lastError.message}. Refresh?`;console.error(chrome.runtime.lastError);}else if(r&&r.status==="started"){statEl.textContent='Inspector started.';window.close();}else if(r&&r.status==="already_active"){statEl.textContent='Inspector active.';window.close();}else{statEl.textContent='Failed: No response.';console.warn(r);}});}});}
document.addEventListener('DOMContentLoaded',()=>{displaySelectors();checkConnection();});
EOF
cat << 'EOF' > whatnot_extension/content.js
// FoSBot Whatnot Helper Content Script v0.4 (Webapp Config)
let selectors = {}; const STORAGE_KEY = 'whatnotSelectors'; let WS_URL = 'ws://localhost:8000/ws/whatnot'; let socket = null; let reconnectTimer = null; let reconnectAttempts = 0; const MAX_RECONNECT_ATTEMPTS = 15; const RECONNECT_DELAY_BASE = 3000; let observer = null; let isInspectorMode = false; let inspectorStep = 0;
const inspectorSteps = [ { key: 'chatContainer', prompt: 'Click MAIN chat message area' }, { key: 'messageItem', prompt: 'Click ANY single chat message row' }, { key: 'username', prompt: 'Click USERNAME in that message' }, { key: 'messageText', prompt: 'Click MESSAGE TEXT in that message' }, { key: 'chatInput', prompt: 'Click the text INPUT field' }, { key: 'sendButton', prompt: 'Click the SEND button/icon' } ];
let inspectorOverlay = null; let lastClickedElementForStep = {};
function initialize() { console.log("FoSBot WN Helper: Init"); loadSelectors().then(loaded => { connectWebSocket(); }); setupMessageListener(); }
function connectWebSocket() { clearTimeout(reconnectTimer); if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) return; console.log(`WN Ext: Connecting WS: ${WS_URL}`); try { socket = new WebSocket(WS_URL); } catch (e) { console.error(`WN Ext: WS connect failed: ${e}`); scheduleReconnect(); return; }
    socket.onopen = () => { console.log('WN Ext: WS Connected'); reconnectAttempts = 0; startObserver(); };
    socket.onmessage = (event) => { console.debug('WN Ext: Msg from server:', event.data); try { const data = JSON.parse(event.data); if (data.action === 'postToWhatnot') { handlePostToWhatnot(data.message); } } catch (e) { console.error("WN Ext: Error parsing server msg", e); } };
    socket.onclose = (event) => { console.log(`WN Ext: WS closed (Code: ${event.code})`); stopObserver(); socket = null; scheduleReconnect(); };
    socket.onerror = (error) => { console.error('WN Ext: WS Error:', error); };
}
function scheduleReconnect() { if (isInspectorMode) return; reconnectAttempts++; if (reconnectAttempts <= MAX_RECONNECT_ATTEMPTS) { const delay = Math.min(RECONNECT_DELAY_BASE * Math.pow(1.5, reconnectAttempts -1), 60000); console.log(`WN Ext: Reconnect attempt ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${delay / 1000}s...`); clearTimeout(reconnectTimer); reconnectTimer = setTimeout(connectWebSocket, delay); } else { console.error("WN Ext: Max WS reconnect attempts."); } }
function handlePostToWhatnot(message) { console.log(`WN Ext: Attempt post: "${message}"`); if (!validateSelectors(['chatInput', 'sendButton'])) { console.error("Cannot post: Selectors invalid."); return false; } const chatInput = document.querySelector(selectors.chatInput); const sendButton = document.querySelector(selectors.sendButton); if (!chatInput || !sendButton) { console.error(`Cannot find Input/Button: ${selectors.chatInput} / ${selectors.sendButton}`); return false; }
    try { chatInput.focus(); const setter = Object.getOwnPropertyDescriptor(window.HTMLInputElement.prototype, "value").set; setter.call(chatInput, message); chatInput.dispatchEvent(new Event('input', { bubbles: true, composed: true })); chatInput.dispatchEvent(new Event('change', { bubbles: true, composed: true }));
        setTimeout(() => { if (!sendButton.disabled) sendButton.click(); else console.warn("WN Send disabled."); }, 150); return true;
    } catch (e) { console.error("Error posting to WN:", e); return false; }
}
async function loadSelectors() { try { const result = await chrome.storage.local.get([STORAGE_KEY]); if (result[STORAGE_KEY] && typeof result[STORAGE_KEY] === 'object') { const keys = Object.keys(selectors); if (keys.every(k => Object.keys(result[STORAGE_KEY]).includes(k))) { selectors = result[STORAGE_KEY]; console.log('WN Ext: Loaded selectors:', selectors); return validateSelectors(keys); } } console.warn('WN Ext: No valid selectors.'); return false; } catch (e) { console.error("WN Ext: Error loading selectors:", e); return false; } }
function validateSelectors(keysToCheck) { return keysToCheck.every(key => selectors[key] && typeof selectors[key] === 'string' && selectors[key].trim() !== ''); }
async function saveSelectors() { try { await chrome.storage.local.set({ [STORAGE_KEY]: selectors }); console.log('WN Ext: Selectors saved:', selectors); if (inspectorOverlay) updateInspectorStatus('Saved! Restarting observer...'); stopObserver(); startObserver(); } catch (e) { console.error("WN Ext: Error saving selectors:", e); if (inspectorOverlay) updateInspectorStatus('ERROR saving!'); } }
function startObserver() { stopObserver(); if (!socket || socket.readyState !== WebSocket.OPEN) return; if (!validateSelectors(['chatContainer', 'messageItem', 'username', 'messageText'])) { console.warn('Observer not started: Read selectors invalid.'); return; } const container = document.querySelector(selectors.chatContainer); if (!container) { console.error(`Observer failed: Cannot find container: ${selectors.chatContainer}`); return; } console.log(`WN Ext: Starting Observer on: ${selectors.chatContainer}`);
    observer = new MutationObserver((mutations) => { for (const m of mutations) { if (m.addedNodes.length) { m.addedNodes.forEach(node => { if (node.nodeType === 1) { if (node.matches(selectors.messageItem)) { parseAndSend(node); } else { node.querySelectorAll(selectors.messageItem).forEach(parseAndSend); } } }); } } });
    observer.observe(container, { childList: true, subtree: true }); console.log("WN Ext: Observer active.");
}
function parseAndSend(el) { const userEl = el.querySelector(selectors.username); const textEl = el.querySelector(selectors.messageText); const user = userEl?.textContent?.trim(); const text = textEl?.textContent?.trim(); if (user && text && text !== user && socket && socket.readyState === WebSocket.OPEN) { console.debug(`WN Ext: Sending: [${user}] ${text}`); socket.send(JSON.stringify({ platform: 'whatnot', user: user, text: text })); } }
function stopObserver() { if (observer) { observer.disconnect(); observer = null; console.log("WN Ext: Observer stopped."); } }
function startInspectorMode() { if (isInspectorMode) return; isInspectorMode = true; inspectorStep = 0; lastClickedElementForStep = {}; console.log("WN Ext: Starting Inspector"); createInspectorOverlay(); updateInspectorPrompt(); document.body.style.cursor = 'crosshair'; document.addEventListener('click', inspectorClickListener, { capture: true }); }
function stopInspectorMode(save = false) { if (!isInspectorMode) return; isInspectorMode = false; document.body.style.cursor = 'default'; document.removeEventListener('click', inspectorClickListener, { capture: true }); removeInspectorOverlay(); console.log("WN Ext: Inspector Stopped."); if (save) { saveSelectors(); } }
function createInspectorOverlay() { removeInspectorOverlay(); inspectorOverlay = document.createElement('div'); inspectorOverlay.style.cssText = `all: initial; position: fixed; top: 10px; left: 10px; background-color: rgba(0, 0, 0, 0.85); color: white; padding: 15px; border: 3px solid gold; border-radius: 5px; z-index: 2147483647; font-family: sans-serif; font-size: 14px; line-height: 1.4; max-width: 350px; box-shadow: 0 0 15px rgba(0,0,0,0.5);`; inspectorOverlay.innerHTML = `<h4 style="all: revert; margin: 0 0 10px 0; padding-bottom: 5px; border-bottom: 1px solid gold;">Configure Selectors</h4><p id="inspectorPrompt" style="all: revert; margin: 5px 0; font-weight: bold;"></p><p id="inspectorStatus" style="all: revert; margin: 10px 0 0 0; font-style: italic; color: #ddd;"></p><button id="cancelInspector" style="all: revert; margin-top: 15px; padding: 5px 8px; background-color: #cc5555; color: white; border: 1px solid #aa4444; cursor: pointer; border-radius: 3px; font-size: 12px;">Cancel</button>`; document.body.appendChild(inspectorOverlay); inspectorOverlay.querySelector('#cancelInspector').addEventListener('click', (e) => { e.stopPropagation(); stopInspectorMode(false); }); }
function removeInspectorOverlay() { if (inspectorOverlay) { inspectorOverlay.remove(); inspectorOverlay = null; } }
function updateInspectorPrompt() { if (!inspectorOverlay) return; const promptEl = inspectorOverlay.querySelector('#inspectorPrompt'); const cancelBtn = inspectorOverlay.querySelector('#cancelInspector'); if (inspectorStep < inspectorSteps.length) { promptEl.textContent = `Step ${inspectorStep + 1}/${inspectorSteps.length}: ${inspectorSteps[inspectorStep].prompt}`; } else { promptEl.textContent = 'All steps done! Review selectors.'; updateInspectorStatus('Click Save to apply.'); const saveBtn = document.createElement('button'); saveBtn.textContent = 'Save Selectors'; saveBtn.style.cssText = 'all: revert; margin-left: 10px; padding: 5px 8px; background-color: #4CAF50; color: white; border: 1px solid #388E3C; cursor: pointer; border-radius: 3px; font-size: 12px;'; saveBtn.onclick = (e) => { e.stopPropagation(); stopInspectorMode(true); }; cancelBtn.insertAdjacentElement('afterend', saveBtn); } }
function updateInspectorStatus(text) { if (!inspectorOverlay) return; inspectorOverlay.querySelector('#inspectorStatus').textContent = text; }
function generateRobustSelector(el) { if (!el || typeof el.getAttribute !== 'function') return null; try { if (el.id) { const idSel = `#${CSS.escape(el.id)}`; if (document.querySelectorAll(idSel).length === 1) return idSel; } const dataAttrs = Array.from(el.attributes).filter(a => a.name.startsWith('data-test') && a.value); for (const a of dataAttrs) { const s = `${el.tagName.toLowerCase()}[${a.name}="${CSS.escape(a.value)}"]`; if (document.querySelectorAll(s).length === 1) return s; } const role = el.getAttribute('role'); if (role) { const s = `${el.tagName.toLowerCase()}[role="${CSS.escape(role)}"]`; if (document.querySelectorAll(s).length === 1) return s; } if (el.classList.length > 0) { const classes = Array.from(el.classList).filter(c => !/^(?:js-|is-|has-|active|focus|hover|animating)/.test(c) && !/\d/.test(c) && c.length > 3); if (classes.length > 0) { return `${el.tagName.toLowerCase()}.${classes.map(c => CSS.escape(c)).join('.')}`; } } return el.tagName.toLowerCase(); } catch (e) { console.error("Error generating selector:", e, el); return null; } }
function generateRelativeSelector(target, base) { if (!base || !target || !base.contains(target)) { return generateRobustSelector(target); } try { if (target.id && base.querySelectorAll(`#${CSS.escape(target.id)}`).length === 1) return `#${CSS.escape(target.id)}`; const dataAttrs = Array.from(target.attributes).filter(a => a.name.startsWith('data-test') && a.value); for (const a of dataAttrs) { const s = `[${a.name}="${CSS.escape(a.value)}"]`; if (base.querySelectorAll(s).length === 1 && base.querySelector(s) === target) return s; } if (target.classList.length > 0) { const classes = Array.from(target.classList).filter(c => !/^(?:js-|is-|has-|active|focus|hover|animating)/.test(c) && !/\d/.test(c) && c.length > 3); if (classes.length > 0) { const s = `.${classes.map(c => CSS.escape(c)).join('.')}`; if (base.querySelectorAll(s).length === 1 && base.querySelector(s) === target) return s; } } return generateRobustSelector(target); } catch (e) { console.error("Error generating relative selector:", e); return generateRobustSelector(target); } }
function inspectorClickListener(event) { if (!isInspectorMode) return; event.preventDefault(); event.stopPropagation(); const targetElement = event.target; const currentStep = inspectorSteps[inspectorStep]; let selector; targetElement.style.outline = '3px dashed gold'; setTimeout(() => { targetElement.style.outline = ''; }, 750); if (currentStep.key === 'username' || currentStep.key === 'messageText') { const baseElement = lastClickedElementForStep['messageItem']; selector = generateRelativeSelector(targetElement, baseElement); } else { selector = generateRobustSelector(targetElement); lastClickedElementForStep[currentStep.key] = targetElement; } selectors[currentStep.key] = selector; updateInspectorStatus(`Selected ${currentStep.key}: ${selector}`); inspectorStep++; updateInspectorPrompt(); }
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => { console.log("WN Ext: Received message:", request); if (request.action === "start_inspector") { if (isInspectorMode) { sendResponse({ status: "already_active" }); if(inspectorOverlay) inspectorOverlay.style.zIndex = '2147483647'; } else { startInspectorMode(); sendResponse({ status: "started" }); } return true; } else if (request.action === "query_status") { sendResponse({ ws_status: socket ? ["CONNECTING", "OPEN", "CLOSING", "CLOSED"][socket.readyState] : "Not Init", selectors_ok: validateSelectors(Object.keys(selectors)) }); return false; } });
initialize(); // Start
EOF
check_success "Failed writing whatnot_extension/content.js"

# --- Create Static Files (Dashboard UI) ---
echo "    Creating static/index.html (with Settings UI)..."
# ... (cat EOF > static/index.html ... same as before) ...
cat << 'EOF' > static/index.html
<!DOCTYPE html><html lang="en"><head><meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>FoSBot Dashboard</title><style>body{font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Oxygen,Ubuntu,Cantarell,Fira Sans,Droid Sans,Helvetica Neue,sans-serif;margin:0;display:flex;flex-direction:column;height:100vh;background-color:#f0f2f5;font-size:14px}button{cursor:pointer;padding:8px 15px;border:none;border-radius:4px;font-weight:600;transition:background-color .2s ease}input[type=text],input[type=password],input[type=url]{padding:8px 10px;border:1px solid #ccc;border-radius:3px;font-size:14px;width:calc(100% - 22px);margin-bottom:8px}label{display:block;margin-bottom:3px;font-weight:600;font-size:.9em;color:#555}#header{background-color:#2c3e50;color:#ecf0f1;padding:8px 15px;display:flex;justify-content:space-between;align-items:center;box-shadow:0 2px 4px rgba(0,0,0,.1)}#header h1{margin:0;font-size:1.4em}#status-indicators{display:flex;gap:12px;font-size:.8em}#status-indicators span{display:flex;align-items:center}.status-light{width:10px;height:10px;border-radius:50%;margin-right:4px;border:1px solid rgba(0,0,0,.1)}.status-text{color:#bdc3c7}.status-disconnected,.status-disabled{background-color:#7f8c8d}.status-connected{background-color:#2ecc71}.status-connecting{background-color:#f39c12;animation:pulseConnect 1.5s infinite}.status-error,.status-crashed,.status-auth_error{background-color:#e74c3c;animation:pulseError 1s infinite}.status-disconnecting{background-color:#e67e22}@keyframes pulseConnect{0%{opacity:.5}50%{opacity:1}100%{opacity:.5}}@keyframes pulseError{0%{transform:scale(.8)}50%{transform:scale(1.1)}100%{transform:scale(.8)}}#main-content{display:flex;flex:1;overflow:hidden}#tab-buttons{background-color:#e1e5eb;padding:5px 10px;border-bottom:1px solid #d1d9e6}#tab-buttons button{background:0 0;border:none;padding:8px 12px;cursor:pointer;font-size:1em;border-bottom:3px solid transparent;margin-right:5px}#tab-buttons button.active{border-bottom-color:#3498db;font-weight:700;color:#2980b9}#content-area{flex:1;display:flex;overflow:hidden}#chat-container{flex:3;display:flex;flex-direction:column;border-right:1px solid #d1d9e6}.tab-content{display:none;height:100%;flex-direction:column;overflow:hidden}.tab-content.active{display:flex}#chat-output{flex:1;overflow-y:auto;padding:10px 15px;background-color:#fff;line-height:1.6}#chat-output div{margin-bottom:6px;word-wrap:break-word;padding:3px 0}#chat-output .platform-tag{font-weight:700;margin-right:5px;display:inline-block;min-width:35px;text-align:right}.twitch{color:#9146ff}.youtube{color:#f00}.x{color:#1da1f2}.whatnot{color:#ff6b00}.streamer_admin{color:#f39c12}.system{color:#7f8c8d}.streamer-msg{background-color:#fff9e6;padding:4px 8px;border-left:3px solid #f1c40f;border-radius:3px;margin-left:-8px;margin-right:-8px}.timestamp{font-size:.75em;color:#95a5a6;margin-left:8px;float:right;opacity:.7}a{color:#3498db;text-decoration:none}a:hover{text-decoration:underline}#input-area{display:flex;padding:10px;border-top:1px solid #d1d9e6;background-color:#ecf0f1}#streamerInput{flex:1;margin-right:8px}#sendButton{background-color:#27ae60;color:#fff}#sendButton:hover{background-color:#2ecc71}#clearButton{background-color:#e67e22;color:#fff;margin-left:5px}#clearButton:hover{background-color:#f39c12}#settings-container{padding:20px;overflow-y:auto;background-color:#fff}.settings-section{margin-bottom:25px;padding-bottom:15px;border-bottom:1px solid #eee}.settings-section h3{margin-top:0;color:#2c3e50;font-size:1.1em}.settings-section button{background-color:#3498db;color:#fff;margin-top:10px}.settings-section button:hover{background-color:#2980b9}.form-group{margin-bottom:10px}#sidebar{flex:1;padding:15px;background-color:#f8f9fa;border-left:1px solid #d1d9e6;overflow-y:auto;font-size:12px;min-width:250px}#sidebar h3{margin-top:0;margin-bottom:10px;color:#2c3e50;border-bottom:1px solid #eee;padding-bottom:5px}#log-output{height:200px;overflow-y:scroll;border:1px solid #eee;padding:8px;margin-top:10px;font-family:Menlo,Monaco,Consolas,Courier New,monospace;background-color:#fff;border-radius:3px;margin-bottom:15px}.log-error{color:#c0392b;font-weight:700}.log-warning{color:#f39c12}.log-info{color:#2980b9}</style></head><body><div id="header"><h1>FoSBot Dashboard</h1><div id="status-indicators"><span id="status-ws">WS: <span class="status-light status-disconnected"></span><span class="status-text">Offline</span></span> <span id="status-twitch">Twitch: <span class="status-light status-disabled"></span><span class="status-text">Off</span></span> <span id="status-youtube">YouTube: <span class="status-light status-disabled"></span><span class="status-text">Off</span></span> <span id="status-x">X: <span class="status-light status-disabled"></span><span class="status-text">Off</span></span> <span id="status-whatnot">Whatnot: <span class="status-light status-disabled"></span><span class="status-text">Ext</span></span></div></div><div id="tab-buttons"><button class="tab-button active" data-tab="chat">Chat</button> <button class="tab-button" data-tab="settings">Settings</button></div><div id="content-area"><div id="chat-container" class="tab-content active" data-tab-content="chat"><div id="chat-output"><div>Welcome! Attempting to connect to backend...</div></div><div id="input-area"><input type="text" id="streamerInput" placeholder="Type message or command (e.g., !roll) to send..."><button id="sendButton">Send</button><button id="clearButton">Clear Display</button></div></div><div id="settings-container" class="tab-content" data-tab-content="settings"><h2>Application Settings</h2><p id="settings-status" style="font-style:italic;"></p><div class="settings-section"><h3>Twitch</h3><form id="twitch-settings-form"><div class="form-group"><label for="twitch-nick">Bot Username (TWITCH_NICK)</label><input type="text" id="twitch-nick" name="TWITCH_NICK"></div><div class="form-group"><label for="twitch-token">Bot OAuth Token (TWITCH_TOKEN)</label><input type="password" id="twitch-token" name="TWITCH_TOKEN" placeholder="oauth:xxxxxxxxxxxx"></div><div class="form-group"><label for="twitch-client-id">Client ID (TWITCH_CLIENT_ID)</label><input type="text" id="twitch-client-id" name="TWITCH_CLIENT_ID"></div><div class="form-group"><label for="twitch-channels">Channel(s) to Join (TWITCH_CHANNELS, comma-separated)</label><input type="text" id="twitch-channels" name="TWITCH_CHANNELS"></div><button type="submit">Save Twitch Settings</button></form></div><div class="settings-section"><h3>YouTube</h3><form id="youtube-settings-form"><div class="form-group"><label for="youtube-api-key">API Key (YOUTUBE_API_KEY)</label><input type="text" id="youtube-api-key" name="YOUTUBE_API_KEY"></div><div class="form-group"><label for="youtube-secrets-file">Client Secrets File Path (YOUTUBE_CLIENT_SECRETS_FILE)</label><input type="text" id="youtube-secrets-file" name="YOUTUBE_CLIENT_SECRETS_FILE" placeholder="/path/to/your/client_secret.json"></div><div class="form-group"><label for="youtube-chat-id">Live Chat ID (YOUTUBE_LIVE_CHAT_ID, optional)</label><input type="text" id="youtube-chat-id" name="YOUTUBE_LIVE_CHAT_ID" placeholder="Leave blank to auto-detect"></div><button type="submit">Save YouTube Settings</button></form></div><div class="settings-section"><h3>X / Twitter</h3><form id="x-settings-form"><div class="form-group"><label for="x-bearer">Bearer Token (X_BEARER_TOKEN)</label><input type="text" id="x-bearer" name="X_BEARER_TOKEN"></div><div class="form-group"><label for="x-api-key">API Key (X_API_KEY)</label><input type="text" id="x-api-key" name="X_API_KEY"></div><div class="form-group"><label for="x-api-secret">API Secret (X_API_SECRET)</label><input type="password" id="x-api-secret" name="X_API_SECRET"></div><div class="form-group"><label for="x-access-token">Access Token (X_ACCESS_TOKEN)</label><input type="text" id="x-access-token" name="X_ACCESS_TOKEN"></div><div class="form-group"><label for="x-access-secret">Access Secret (X_ACCESS_SECRET)</label><input type="password" id="x-access-secret" name="X_ACCESS_SECRET"></div><div class="form-group"><label for="x-monitor">Hashtag/Mention to Monitor (X_HASHTAG_OR_MENTION)</label><input type="text" id="x-monitor" name="X_HASHTAG_OR_MENTION" placeholder="#YourTag or @YourBot"></div><button type="submit">Save X/Twitter Settings</button></form></div><div class="settings-section"><h3>Service Control</h3><p>Restart services after changing credentials.</p><button class="control-button" data-service="twitch" data-command="start">Start Twitch</button> <button class="control-button" data-service="twitch" data-command="stop">Stop Twitch</button> <button class="control-button" data-service="twitch" data-command="restart">Restart Twitch</button><br><button class="control-button" data-service="youtube" data-command="start">Start YouTube</button> <button class="control-button" data-service="youtube" data-command="stop">Stop YouTube</button> <button class="control-button" data-service="youtube" data-command="restart">Restart YouTube</button><br><button class="control-button" data-service="x" data-command="start">Start X</button> <button class="control-button" data-service="x" data-command="stop">Stop X</button> <button class="control-button" data-service="x" data-command="restart">Restart X</button><br></div></div><div id="sidebar"><h3>Status & Logs</h3><div id="general-status">App Status: Initializing...</div><div id="log-output"></div></div></div><script src="main.js"></script></body></html>
EOF
check_success "Failed writing static/index.html"

echo "    Creating static/main.js..."
# Paste the full updated main.js from previous response here
cat << 'EOF' > static/main.js
// FoSBot Dashboard Frontend JS v0.4 (Webapp Config)
const chatOutput=document.getElementById('chat-output');const streamerInput=document.getElementById('streamerInput');const sendButton=document.getElementById('sendButton');const clearButton=document.getElementById('clearButton');const wsStatusElement=document.getElementById('status-ws').querySelector('.status-text');const wsLightElement=document.getElementById('status-ws').querySelector('.status-light');const platformStatus={twitch:document.getElementById('status-twitch'),youtube:document.getElementById('status-youtube'),x:document.getElementById('status-x'),whatnot:document.getElementById('status-whatnot')};const generalStatus=document.getElementById('general-status');const logOutput=document.getElementById('log-output');const tabButtons=document.querySelectorAll('.tab-button');const tabContents=document.querySelectorAll('.tab-content');const settingsStatus=document.getElementById('settings-status');const twitchForm=document.getElementById('twitch-settings-form');const youtubeForm=document.getElementById('youtube-settings-form');const xForm=document.getElementById('x-settings-form');const controlButtons=document.querySelectorAll('.control-button');let socket=null;let reconnectTimer=null;let reconnectAttempts=0;const MAX_RECONNECT_ATTEMPTS=10;const RECONNECT_DELAY_BASE=3000;
function updateStatus(id,cls,txt=''){const i=platformStatus[id];if(i){const t=i.querySelector('.status-text');const l=i.querySelector('.status-light');l.className='status-light';l.classList.add(`status-${cls}`);t.textContent=txt||cls.charAt(0).toUpperCase()+cls.slice(1);}else if(id==='ws'){wsLightElement.className='status-light';wsLightElement.classList.add(`status-${cls}`);wsStatusElement.textContent=txt||cls.charAt(0).toUpperCase()+cls.slice(1);}}
function formatTimestamp(iso){if(!iso)return '';try{const d=new Date(iso);if(isNaN(d.getTime()))return '';return d.toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});}catch(e){console.error("TS fmt err:",e);return '';}}
function addChatMessage(p,u,t,ts=null){const d=document.createElement('div');const ps=document.createElement('span');const us=document.createElement('span');const ts_span=document.createElement('span');const tm=document.createElement('span');const pCls=p?p.toLowerCase().replace(/[^a-z0-9]/g,''):'system';ps.classList.add('platform-tag',pCls);ps.textContent=`[${p?p.toUpperCase():'SYS'}]`;us.style.fontWeight='bold';us.textContent=` ${u}: `;const sT=t.replace(/</g,"<").replace(/>/g,">");const urlRgx=/(\b(https?|ftp|file):\/\/[-A-Z0-9+&@#\/%?=~_|!:,.;]*[-A-Z0-9+&@#\/%=~_|])/ig;ts_span.innerHTML=sT.replace(urlRgx,'<a href="$1" target="_blank" rel="noopener noreferrer">$1</a>');tm.classList.add('timestamp');tm.textContent=formatTimestamp(ts);d.appendChild(tm);d.appendChild(ps);d.appendChild(us);d.appendChild(ts_span);const streamerU="STREAMER";if(u&&u.toLowerCase()===streamerU.toLowerCase()){d.classList.add('streamer-msg');}const scroll=chatOutput.scrollTop+chatOutput.clientHeight>=chatOutput.scrollHeight-50;chatOutput.appendChild(d);if(scroll){chatOutput.scrollTop=chatOutput.scrollHeight;}}
function addLogMessage(l,m,mod=''){const le=document.createElement('div');const lu=l.toUpperCase();le.classList.add(`log-${l.toLowerCase()}`);const tm=new Date().toLocaleTimeString([],{hour:'2-digit',minute:'2-digit',second:'2-digit'});le.textContent=`[${tm}] [${lu}] ${mod?'['+mod+'] ':''}${m}`;logOutput.appendChild(le);const MAX_LOG=150;while(logOutput.children.length>MAX_LOG){logOutput.removeChild(logOutput.firstChild);}logOutput.scrollTop=logOutput.scrollHeight;}
function handleWebSocketMessage(data){switch(data.type){case 'chat':addChatMessage(data.platform,data.user,data.text,data.timestamp);break;case 'platform_status':updateStatus(data.platform,data.status.toLowerCase(),data.status);addLogMessage('INFO',`Platform [${data.platform.toUpperCase()}]: ${data.status} ${data.message?'- '+data.message:''}`);break;case 'log':addLogMessage(data.level,data.message,data.module);break;case 'status':addLogMessage('INFO',`Backend: ${data.message}`);generalStatus.textContent=`App Status: ${data.message}`;break;case 'error':addLogMessage('ERROR',`Backend Err: ${data.message}`);generalStatus.textContent=`App Status: Error - ${data.message}`;break;case 'pong':console.log("Pong.");break;case 'current_settings':populateSettingsForm(data.payload||{});break;default:console.warn("Unknown WS type:",data.type,data);addLogMessage('WARN',`Unknown WS type: ${data.type}`);}}
function connectWebSocket(){clearTimeout(reconnectTimer);if(socket&&(socket.readyState===WebSocket.OPEN||socket.readyState===WebSocket.CONNECTING))return;const wsProto=window.location.protocol==='https:'?'wss:':'ws:';const wsUrl=`${wsProto}//localhost:8000/ws/dashboard`;console.log(`Connecting WS: ${wsUrl}`);updateStatus('ws','connecting','Connecting...');addLogMessage('INFO',`Connecting WS...`);generalStatus.textContent="Connecting...";socket=new WebSocket(wsUrl);socket.onopen=()=>{console.log('WS Open');updateStatus('ws','connected','Online');addLogMessage('INFO','WS connected.');reconnectAttempts=0;generalStatus.textContent="Connected";requestSettings();};socket.onmessage=(e)=>{try{const d=JSON.parse(e.data);handleWebSocketMessage(d);}catch(err){console.error("WS Parse Err:",err);addLogMessage("ERROR","Bad WS msg.");}};socket.onclose=(e)=>{console.log(`WS Closed: ${e.code}`);updateStatus('ws','disconnected',`Offline`);addLogMessage('WARN',`WS closed (${e.code}).`);generalStatus.textContent="Disconnected";socket=null;if(reconnectAttempts<MAX_RECONNECT_ATTEMPTS){reconnectAttempts++;const delay=Math.min(RECONNECT_DELAY_BASE*Math.pow(1.5,reconnectAttempts-1),30000);console.log(`WS Reconnect ${reconnectAttempts}/${MAX_RECONNECT_ATTEMPTS} in ${delay/1000}s...`);addLogMessage('INFO',`Attempt reconnect (${reconnectAttempts})...`);reconnectTimer=setTimeout(connectWebSocket,delay);}else{console.error("WS Max reconnects.");addLogMessage('ERROR',"Max WS reconnects.");generalStatus.textContent="Connection Failed";}};socket.onerror=(err)=>{console.error('WS Error:',err);updateStatus('ws','error','Error');addLogMessage('ERROR','WS connection error.');};}
function sendStreamerInput(){const t=streamerInput.value.trim();if(!t)return;if(socket&&socket.readyState===WebSocket.OPEN){const m={type:"streamer_input",text:t};try{socket.send(JSON.stringify(m));streamerInput.value='';addLogMessage('INFO',`Sent: "${t.substring(0,50)}..."`);}catch(e){console.error("WS Send Err:",e);addLogMessage('ERROR',`Send fail: ${e.message}`);}}else{addLogMessage('ERROR',"Cannot send: WS closed.");}}
sendButton.addEventListener('click',sendStreamerInput);streamerInput.addEventListener('keypress',(e)=>{if(e.key==='Enter'&&!e.shiftKey){e.preventDefault();sendStreamerInput();}});clearButton.addEventListener('click',()=>{chatOutput.innerHTML='';addLogMessage('INFO',"Chat display cleared.");});
tabButtons.forEach(b=>{b.addEventListener('click',()=>{const tab=b.getAttribute('data-tab');tabButtons.forEach(btn=>btn.classList.remove('active'));tabContents.forEach(c=>c.classList.remove('active'));b.classList.add('active');document.querySelector(`.tab-content[data-tab-content="${tab}"]`).classList.add('active');if(tab==='settings'){requestSettings();}});});
function requestSettings(){if(socket&&socket.readyState===WebSocket.OPEN){console.log("Requesting settings...");socket.send(JSON.stringify({type:"request_settings"}));}else{showSettingsStatus("Cannot load: WS closed.",true);}}
function populateSettingsForm(s){console.log("Populating settings:",s);twitchForm.elements['TWITCH_NICK'].value=s.TWITCH_NICK||'';twitchForm.elements['TWITCH_TOKEN'].placeholder=s.TWITCH_TOKEN?'********':'oauth:xxxx';twitchForm.elements['TWITCH_TOKEN'].value='';twitchForm.elements['TWITCH_CLIENT_ID'].value=s.TWITCH_CLIENT_ID||'';twitchForm.elements['TWITCH_CHANNELS'].value=s.TWITCH_CHANNELS||'';youtubeForm.elements['YOUTUBE_API_KEY'].value=s.YOUTUBE_API_KEY||'';youtubeForm.elements['YOUTUBE_CLIENT_SECRETS_FILE'].value=s.YOUTUBE_CLIENT_SECRETS_FILE||'';youtubeForm.elements['YOUTUBE_LIVE_CHAT_ID'].value=s.YOUTUBE_LIVE_CHAT_ID||'';xForm.elements['X_BEARER_TOKEN'].value=s.X_BEARER_TOKEN||'';xForm.elements['X_API_KEY'].value=s.X_API_KEY||'';xForm.elements['X_API_SECRET'].placeholder=s.X_API_SECRET?'********':'Enter Secret';xForm.elements['X_API_SECRET'].value='';xForm.elements['X_ACCESS_TOKEN'].value=s.X_ACCESS_TOKEN||'';xForm.elements['X_ACCESS_SECRET'].placeholder=s.X_ACCESS_SECRET?'********':'Enter Secret';xForm.elements['X_ACCESS_SECRET'].value='';xForm.elements['X_HASHTAG_OR_MENTION'].value=s.X_HASHTAG_OR_MENTION||'';showSettingsStatus("Settings loaded (secrets hidden). Enter new values to update.",false);}
async function saveSettings(formEl){const formData=new FormData(formEl);const dataToSend={};let hasChanges=false;formData.forEach((value,key)=>{const inputEl=formEl.elements[key];const isSecret=(inputEl.type==='password');if(value!==''){dataToSend[key]=value;hasChanges=true;}else if(isSecret&&inputEl.placeholder&&!inputEl.placeholder.includes('********')){/*If placeholder wasn't masked, user cleared it - maybe send null?*/}});if(!hasChanges){showSettingsStatus("No changes entered to save.",false);return;}console.log("Saving:",Object.keys(dataToSend));showSettingsStatus("Saving...",false);try{const response=await fetch('/api/settings',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(dataToSend)});const result=await response.json();if(response.ok){showSettingsStatus(result.message||"Saved!",false);formEl.reset();requestSettings();}else{showSettingsStatus(`Error: ${result.detail||response.statusText}`,true);}}catch(error){console.error("Save Settings Err:",error);showSettingsStatus(`Network error: ${error.message}`,true);}}
twitchForm.addEventListener('submit',(e)=>{e.preventDefault();saveSettings(e.target);});youtubeForm.addEventListener('submit',(e)=>{e.preventDefault();saveSettings(e.target);});xForm.addEventListener('submit',(e)=>{e.preventDefault();saveSettings(e.target);});
controlButtons.forEach(b=>{b.addEventListener('click',async(e)=>{const srv=e.target.getAttribute('data-service');const cmd=e.target.getAttribute('data-command');showSettingsStatus(`Sending '${cmd}' to ${srv}...`,false);try{const response=await fetch(`/api/control/${srv}/${cmd}`,{method:'POST'});const result=await response.json();if(response.ok){showSettingsStatus(result.message||`Cmd sent.`,false);}else{showSettingsStatus(`Error: ${result.detail||response.statusText}`,true);}}catch(error){console.error("Control Err:",error);showSettingsStatus(`Network error: ${error.message}`,true);}});});
document.addEventListener('DOMContentLoaded',()=>{addLogMessage('INFO','Dashboard UI Initialized.');connectWebSocket();});
EOF
check_success "Failed writing static/main.js"
# --- Create basic .gitignore ---
echo "    Creating .gitignore..."
cat << EOF > .gitignore
venv/
__pycache__/
*.pyc
*.pyo
*.pyd
.env
*.db
*.db-journal
*.sqlite3
client_secret.json
*.log
*.tmp
# Data directory (contains secrets!)
/${DATA_DIR}/
# IDE files
.vscode/
*.sublime-project
*.sublime-workspace
# OS files
.DS_Store
# Coverage
.coverage
htmlcov/
EOF
check_success "Failed writing .gitignore"
# --- Create basic README ---
echo "    Creating README.md..."
cat << EOF > README.md
# FoSBot - Multi-Platform Stream Chatbot (Webapp Config Version)

Handles chat aggregation and bot commands. API keys and settings are configured via the web UI after launching. Data is stored in JSON files in the \`./${DATA_DIR}\` directory.

## Setup

1.  Run the setup script: \`./setup_fosbot.sh\`
2.  Follow prompts (may require sudo for Homebrew/Xcode tools).
3.  Follow the final manual steps printed by the script (Load browser extension, configure its selectors).

## Running

1.  Activate the virtual environment: \`source venv/bin/activate\`
2.  Start the backend server: \`uvicorn app.main:app --reload --host localhost\`
3.  Open the dashboard in your browser (usually \`http://localhost:8000\`).
4.  Navigate to the **Settings** tab in the dashboard.
5.  Enter your API keys, tokens, bot/channel names, etc., and click "Save" for each section.
6.  Use the "Service Control" buttons (e.g., "Start Twitch") on the Settings tab to activate the platform connections.
7.  Configure the Whatnot extension selectors via its popup while on a Whatnot page.

EOF
check_success "Failed writing README.md"

# --- [10/10] Create Basic Placeholder Icons ---
echo ""; echo "[10/10] Creating placeholder icons..."
if command_exists convert; then ICON_COLOR="rgba(60,80,100,0.8)"; convert -size 16x16 xc:"${ICON_COLOR}" whatnot_extension/icons/icon16.png; convert -size 48x48 xc:"${ICON_COLOR}" whatnot_extension/icons/icon48.png; convert -size 128x128 xc:"${ICON_COLOR}" whatnot_extension/icons/icon128.png; check_success "Failed creating icons."; echo "    Placeholder icons created.";
else echo "    WARNING: ImageMagick 'convert' not found. Skipping icon creation. Create dummy icons manually in whatnot_extension/icons/."; fi

# --- Finish ---
echo ""; echo ""; echo "--- //////////////////////////////////\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\ ---"
echo "--- //    SETUP COMPLETE - CONFIGURE VIA WEB UI NEXT!          \\\\ ---"
echo "--- \\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\\////////////////////////////////// ---"
echo ""; echo "Project files and base dependencies are set up for Phase 1 (Webapp Config / JSON Storage)."
echo ""; echo "NEXT STEPS:"; echo ""
echo "1.  **LOAD BROWSER EXTENSION:**"; echo "    Open Browser -> Extensions -> Dev Mode ON -> Load Unpacked -> Select './whatnot_extension' dir."
echo ""; echo "2.  **RUN THE BACKEND (Activate venv first!):**"; echo "    In Terminal (in ${PROJECT_DIR_NAME} dir):"; echo "    source venv/bin/activate"; echo "    uvicorn app.main:app --reload --host localhost"
echo ""; echo "3.  **ACCESS DASHBOARD & CONFIGURE:**"; echo "    Open browser to: http://localhost:8000"; echo "    Go to the 'Settings' tab."; echo "    Enter your API keys/tokens/settings for Twitch, YouTube, X."; echo "    Place 'client_secret.json' at the path you enter for YouTube."; echo "    Click 'Save' for each section."
echo ""; echo "4.  **START SERVICES:**"; echo "    On the 'Settings' tab, use the 'Start Twitch', 'Start YouTube', etc., buttons."
echo "    Watch the terminal logs and dashboard status indicators."
echo ""; echo "5.  **CONFIGURE WHATNOT SELECTORS (CRITICAL for Whatnot):**"; echo "    Go to a Whatnot stream page."; echo "    Click extension icon -> 'Configure Selectors' -> Follow overlay -> Save."; echo "    (Repeat when Whatnot chat breaks)"
echo ""; echo "--- Your bot is ready for configuration via the dashboard! ---"; echo ""
exit 0