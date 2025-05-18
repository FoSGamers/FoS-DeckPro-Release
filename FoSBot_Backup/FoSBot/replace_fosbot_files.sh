#!/bin/bash

# Script to replace defective FoSBot files with corrected versions
# Date: 2025-04-17
# Author: Grok 3 (assisted by xAI)
# Version: 1.0.0

# Define project directory
PROJECT_DIR="/Users/jgleason/FoSBot"
BACKUP_DIR="$PROJECT_DIR/backup_$(date +%Y%m%d_%H%M)"

# Ensure project directory exists
if [ ! -d "$PROJECT_DIR" ]; then
    echo "Error: Project directory $PROJECT_DIR does not exist."
    exit 1
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"
echo "Backing up existing files to $BACKUP_DIR..."

# Backup function
backup_file() {
    local file="$1"
    if [ -f "$file" ]; then
        local rel_path="${file#$PROJECT_DIR/}"
        local backup_path="$BACKUP_DIR/$rel_path"
        mkdir -p "$(dirname "$backup_path")"
        cp "$file" "$backup_path"
        echo "Backed up $rel_path"
    fi
}

# Backup all existing files
files=(
    ".env"
    ".gitignore"
    "requirements.txt"
    "README.md"
    "combine_files.py"
    "create_fosbot_files.sh"
    "app/__init__.py"
    "app/main.py"
    "app/events.py"
    "app/core/__init__.py"
    "app/core/config.py"
    "app/core/event_bus.py"
    "app/core/json_store.py"
    "app/apis/__init__.py"
    "app/apis/auth_api.py"
    "app/apis/settings_api.py"
    "app/apis/ws_endpoints.py"
    "app/apis/commands_api.py"
    "app/services/__init__.py"
    "app/services/chat_processor.py"
    "app/services/dashboard_service.py"
    "app/services/streamer_command_handler.py"
    "app/services/twitch_service.py"
    "app/services/youtube_service.py"
    "app/services/x_service.py"
    "app/services/whatnot_bridge.py"
    "static/index.html"
    "static/main.js"
    "whatnot_extension/manifest.json"
    "whatnot_extension/background.js"
    "whatnot_extension/popup.html"
    "whatnot_extension/popup.js"
    "whatnot_extension/content.js"
    "data/oauth_states.json"
    "data/settings.json"
    "data/commands.json"
    "data/tokens.json"
)

for file in "${files[@]}"; do
    backup_file "$PROJECT_DIR/$file"
done

# Function to write file with content
write_file() {
    local file_path="$1"
    local content="$2"
    local dir_path="$(dirname "$file_path")"
    mkdir -p "$dir_path"
    echo -e "$content" > "$file_path"
    echo "Created/Updated $file_path"
}

# Write corrected files
# Root Directory Files
write_file "$PROJECT_DIR/.env" "# Version History: 0.7.2 -> 0.7.3
# Application Settings
COMMAND_PREFIX=!
WS_HOST=localhost
WS_PORT=8000
LOG_LEVEL=DEBUG
DATA_DIR=data
TWITCH_CHANNELS=fos_gamers
TWITCH_ACCESS_TOKEN=<your_token>
YOUTUBE_API_KEY=<your_key>
X_API_KEY=<your_key>
X_API_SECRET=<your_secret>
X_ACCESS_TOKEN=<your_token>
X_ACCESS_TOKEN_SECRET=<your_secret>"

write_file "$PROJECT_DIR/.gitignore" "# Version History: 0.7.2 -> 0.7.3
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
venv/
*.egg-info/
.env
data/*
*.zip"

write_file "$PROJECT_DIR/requirements.txt" "# Version History: 0.7.2 -> 0.7.3
fastapi>=0.110.0
uvicorn[standard]>=0.29.0
python-dotenv>=1.0.0
twitchio>=2.10.0
google-api-python-client>=2.80.0
google-auth-oauthlib>=1.0.0
google-auth-httplib2>=0.1.0
tweepy>=4.13.0
websockets>=11.0.0
httpx>=0.27.0
requests-oauthlib>=1.3.0
aiohttp>=3.8.0
nest-asyncio>=1.5.0
aiofiles>=23.1.0
pydantic>=2.0.0
typing-extensions>=4.8.0
click>=7.0
h11>=0.8
httptools>=0.5.0
pyyaml>=5.1
uvloop>=0.17.0
watchfiles>=0.13
certifi
googleapis-common-protos>=1.56.2,<2.0.0
protobuf>=3.19.5,<7.0.0
proto-plus>=1.22.3,<2.0.0
cachetools>=2.0.0,<6.0
pyasn1-modules>=0.2.1
rsa>=3.1.4,<5
pyparsing!=3.0.0,!=3.0.1,!=3.0.2,!=3.0.3,<4,>=2.4.2
charset-normalizer<4,>=2
urllib3<3,>=1.21.1
sniffio>=1.1
pyasn1>=0.6.1,<0.7.0
attrs>=17.3.0
frozenlist>=1.1.1
multidict<7.0,>=4.5
yarl<2.0,>=1.0
annotated-types>=0.4.0
typing-inspection>=0.4.0
idna
aiosignal>=1.1.2
oauthlib<4,>=3.2.0
requests<3,>=2.27.0
httpcore>=1.0.0,<2.0.0
aiohappyeyeballs>=2.3.0
propcache>=0.2.0"

write_file "$PROJECT_DIR/README.md" "# Version History: 0.7.2 -> 0.7.3
# FoSBot: Your Epic Stream Chat Adventure

Welcome, brave streamer, to **FoSBot**—the ultimate companion for your Magic: The Gathering and Dungeons & Dragons live streams! This bot unites Whatnot, YouTube, Twitch, and X chats into one magical dashboard, letting you engage your party with commands like \`!checkin\`, \`!ping\`, and \`!roll\`. Roll for initiative and let's get started!

## Your Quest: Setup (Level 1 - Easy)

### Prerequisites
- **Python 3.13**: Your trusty spellbook. Install it from [python.org](https://www.python.org/downloads/) or via Homebrew (\`brew install python@3.13\`).
- **Chrome Browser**: Your enchanted portal to the dashboard.

### Step 1: Unpack the Treasure
1. **Grab the Loot**:
   - Download \`fosbot.zip\` from our Patreon ([insert your Patreon link]).
   - Unzip it to a folder, like \`~/FoSBot\`:
     \`\`\`bash
     unzip fosbot.zip -d ~/FoSBot
     \`\`\`

### Step 2: Cast the Setup Spell
1. **Enter the Dungeon**:
   - Open Terminal (Mac: Spotlight > \"Terminal\").
   - Navigate to your folder:
     \`\`\`bash
     cd ~/FoSBot
     \`\`\`
2. **Prepare Your Magic**:
   - Create a virtual environment and install dependencies:
     \`\`\`bash
     /opt/homebrew/bin/python3.13 -m venv venv
     source venv/bin/activate
     pip install -r requirements.txt
     \`\`\`
3. **Launch the Portal**:
   - Run the app:
     \`\`\`bash
     uvicorn app.main:app --host localhost --port 8000
     \`\`\`
     - If you see “Application startup complete,” you’re ready!

### Step 3: Enter the Dashboard
1. **Open the Gate**:
   - In Chrome, go to http://localhost:8000.
2. **Join the Party**:
   - Go to the **Settings** tab.
   - Click “Login with YouTube,” “Login with Twitch,” and “Login with X.” Sign in to each—no developer portals needed, just your account!
3. **Whatnot Enchantment**:
   - In Settings, click “Guided Setup” for step-by-step help or download \`whatnot_extension.zip\`.
   - Unzip to a folder (e.g., \`~/FoSBot_Whatnot\`).
   - In Chrome, go to \`chrome://extensions/\`, enable “Developer mode,” click “Load unpacked,” and select the folder.
   - On a Whatnot stream, click the extension icon (puzzle piece), enable “Select Mode,” click chat elements, and save.
   - **Need Help?** Watch our 1-minute setup video on Patreon ([insert your video link]).

### Step 4: Wield Your Powers
- **Chat Tab**:
  - See all platform chats in real-time.
  - Send messages or commands (e.g., \`!ping\` for “Pong!”).
- **Commands Tab**:
  - Click “Add Command” to create new ones (e.g., \`!roll\` for “Rolled a 15!”).
  - Upload a CSV (\`command,response\`) to add multiple commands.
  - Edit or delete as needed.
- **Settings Tab**:
  - Manage logins, Twitch channels, and services (start/stop/restart).
- **Commands to Try**:
  - \`!checkin\`: Marks your presence in the tavern.
  - \`!ping\`: Tests the bot’s reflexes.
  - \`!roll\`: Rolls a die (e.g., \`!roll d20\`).
  - Add your own in the Commands tab!

## The Playbook: Tips for Glory
- **Engage Your Guild**:
  - Use \`!roll\` for D&D flair (add via Commands tab).
  - Broadcast messages to all platforms from the Chat tab.
- **Troubleshooting**:
  - **Login Issues?** Ensure you’re signed into the right account. Check the video if stuck.
  - **Whatnot Not Working?** Verify selectors in the extension popup.
  - **App Won’t Run?** Confirm Python 3.13 and re-run \`pip install -r requirements.txt\`.
- **Need a Bard?** Post on our Patreon for help!

## Epic Loot (Future Quests)
- Add more commands like \`!quest\` for community challenges.
- Share feedback on Patreon to shape FoSBot’s saga!

**Roll a natural 20 and stream on!**

*Created by [Your Name] for the MTG & D&D crew. No OAuth setup needed—log in and play!*"

write_file "$PROJECT_DIR/combine_files.py" "# Version History: 0.7.2 -> 0.7.3
import os
from pathlib import Path

def combine_files(output_file):
    root_dir = Path('.')
    with open(output_file, 'w') as outfile:
        for filepath in root_dir.rglob('*'):
            if filepath.is_file() and filepath.suffix in ['.py', '.html', '.js', '.json']:
                with open(filepath, 'r') as infile:
                    outfile.write(f\"\n\n# {filepath}\n\")
                    outfile.write(infile.read())

if __name__ == \"__main__\":
    combine_files('project_files.txt')"

write_file "$PROJECT_DIR/create_fosbot_files.sh" "# Version History: 0.7.2 -> 0.7.3
#!/bin/bash

mkdir -p app/core app/services app/apis static whatnot_extension data
touch app/__init__.py app/main.py app/events.py
touch app/core/__init__.py app/core/config.py app/core/event_bus.py app/core/json_store.py
touch app/services/__init__.py app/services/chat_processor.py app/services/dashboard_service.py
touch app/services/streamer_command_handler.py app/services/twitch_service.py
touch app/services/youtube_service.py app/services/x_service.py app/services/whatnot_bridge.py
touch app/apis/__init__.py app/apis/auth_api.py app/apis/settings_api.py
touch app/apis/ws_endpoints.py app/apis/commands_api.py
touch static/index.html static/main.js
touch whatnot_extension/manifest.json whatnot_extension/background.js
touch whatnot_extension/popup.html whatnot_extension/popup.js whatnot_extension/content.js
touch data/oauth_states.json data/settings.json data/commands.json data/tokens.json
touch requirements.txt README.md combine_files.py create_fosbot_files.sh .env .gitignore"

# app/ Directory Files
write_file "$PROJECT_DIR/app/__init__.py" "# Version History: 0.7.2 -> 0.7.3
# Empty file to make app a package"

write_file "$PROJECT_DIR/app/main.py" "# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi.exceptions import HTTPException

# Core Imports
from app.core.config import logger, settings
from app.core.event_bus import event_bus

# API Routers
from app.apis import ws_endpoints, settings_api, auth_api, commands_api

# Service Control & Setup
from app.services.twitch_service import start_twitch_service_task, stop_twitch_service
from app.services.youtube_service import start_youtube_service_task, stop_youtube_service
from app.services.x_service import start_x_service_task, stop_x_service
from app.services.whatnot_bridge import start_whatnot_bridge_task, stop_whatnot_bridge
from app.services.chat_processor import setup_chat_processor
from app.services.dashboard_service import setup_dashboard_service_listeners
from app.services.streamer_command_handler import setup_streamer_command_handler

# Events
from app.events import ServiceControl

# Global State
background_tasks = set()
_service_tasks_map: dict[str, asyncio.Task | None] = {}

# Service Control Mapping
service_control_map = {
    \"twitch\": {\"start\": start_twitch_service_task, \"stop\": stop_twitch_service},
    \"youtube\": {\"start\": start_youtube_service_task, \"stop\": stop_youtube_service},
    \"x\": {\"start\": start_x_service_task, \"stop\": stop_x_service},
    \"whatnot\": {\"start\": start_whatnot_bridge_task, \"stop\": stop_whatnot_bridge},
}

async def handle_service_control(event: ServiceControl):
    \"\"\"Handles start/stop/restart commands for services via the event bus.\"\"\"
    logger.info(f\"Handling control: '{event.command}' for '{event.service_name}'...\")
    logger.debug(f\"Service control event details: {event}\")
    control_funcs = service_control_map.get(event.service_name)
    current_task = _service_tasks_map.get(event.service_name)

    if not control_funcs:
        logger.error(f\"No control functions found for service '{event.service_name}'.\")
        return

    start_func = control_funcs.get(\"start\")
    stop_func = control_funcs.get(\"stop\")

    if event.command == \"stop\":
        if current_task and not current_task.done():
            logger.info(f\"Stopping running/starting service '{event.service_name}'...\")
            if stop_func:
                try:
                    await stop_func()
                    logger.info(f\"Service '{event.service_name}' stopped successfully.\")
                except Exception as e:
                    logger.error(f\"Error stopping service '{event.service_name}': {e}\")
            else:
                logger.warning(f\"No stop function defined but task exists for '{event.service_name}'. Cancelling directly.\")
                if not current_task.cancelled():
                    current_task.cancel()
        else:
            logger.info(f\"Service '{event.service_name}' not running, no stop action needed.\")
        _service_tasks_map[event.service_name] = None

    elif event.command == \"start\":
        if current_task and not current_task.done():
            logger.warning(f\"Service '{event.service_name}' already running or starting.\")
            return

        if start_func:
            logger.info(f\"Executing start for '{event.service_name}'...\")
            try:
                new_task = start_func()
                if new_task and isinstance(new_task, asyncio.Task):
                    _service_tasks_map[event.service_name] = new_task
                    background_tasks.add(new_task)
                    new_task.add_done_callback(background_tasks.discard)
                    logger.info(f\"Task for '{event.service_name}' started and added to background tasks.\")
                elif new_task is None:
                    logger.warning(f\"Start function for '{event.service_name}' did not return a task (disabled/failed pre-check?).\")
                else:
                    logger.error(f\"Start function for '{event.service_name}' returned invalid object: {type(new_task)}\")
            except Exception as e:
                logger.error(f\"Error starting service '{event.service_name}': {e}\")
        else:
            logger.warning(f\"No start function defined for '{event.service_name}'.\")

    elif event.command == \"restart\":
        logger.info(f\"Executing restart for '{event.service_name}'...\")
        if current_task and not current_task.done():
            logger.info(\"...stopping existing service first.\")
            if stop_func:
                try:
                    await stop_func()
                    await asyncio.sleep(1)
                    logger.info(f\"Service '{event.service_name}' stopped for restart.\")
                except Exception as e:
                    logger.error(f\"Error stopping service '{event.service_name}' for restart: {e}\")
            else:
                logger.warning(f\"No stop function for restart of '{event.service_name}'. Cancelling directly.\")
                if not current_task.cancelled():
                    current_task.cancel()
                await asyncio.sleep(0.1)
        else:
            logger.info(\"...service not running, attempting start.\")

        _service_tasks_map[event.service_name] = None

        if start_func:
            logger.info(\"...starting new service instance.\")
            try:
                new_task = start_func()
                if new_task and isinstance(new_task, asyncio.Task):
                    _service_tasks_map[event.service_name] = new_task
                    background_tasks.add(new_task)
                    new_task.add_done_callback(background_tasks.discard)
                    logger.info(f\"Task for '{event.service_name}' added after restart.\")
                elif new_task is None:
                    logger.warning(f\"Start function for '{event.service_name}' did not return task on restart.\")
                else:
                    logger.error(f\"Start function '{event.service_name}' returned invalid object on restart: {type(new_task)}\")
            except Exception as e:
                logger.error(f\"Error restarting service '{event.service_name}': {e}\")
        else:
            logger.warning(f\"No start function available for restart of '{event.service_name}'.\")

# Lifespan Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    \"\"\"Handles application startup and shutdown events.\"\"\"
    logger.info(\"--- Application startup sequence initiated ---\")
    logger.info(\"Starting event bus worker...\"); await event_bus.start()
    logger.info(\"Setting up event listeners...\")
    try:
        await setup_chat_processor()
        logger.debug(\"Chat processor setup completed\")
    except Exception as e:
        logger.error(f\"Error setting up chat processor: {e}\")
    setup_dashboard_service_listeners()
    setup_streamer_command_handler()
    event_bus.subscribe(ServiceControl, handle_service_control)
    logger.info(\"Service control handler subscribed.\")
    logger.info(\"Services will start only via user action through the dashboard.\")
    logger.info(\"--- Application startup complete. Running! ---\")

    yield

    logger.info(\"--- Application shutdown sequence initiated ---\")
    logger.info(\"Stopping platform services (sending stop commands)...\")
    stop_tasks = [
        handle_service_control(ServiceControl(service_name=name, command=\"stop\"))
        for name in service_control_map.keys()
    ]
    try:
        await asyncio.gather(*stop_tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f\"Error stopping services: {e}\")

    logger.info(\"Waiting briefly...\"); await asyncio.sleep(1)
    logger.info(\"Stopping event bus worker...\"); await event_bus.stop()

    if background_tasks:
        logger.warning(f\"Cancelling {len(background_tasks)} lingering background tasks...\")
        for task in list(background_tasks):
            if task and not task.done():
                task.cancel()
        try:
            await asyncio.wait_for(asyncio.gather(*background_tasks, return_exceptions=True), timeout=5.0)
            logger.debug(\"Cancelled background tasks successfully.\")
        except asyncio.TimeoutError:
            logger.error(\"Timeout waiting for background tasks to cancel.\")
        except Exception as e:
            logger.exception(f\"Error during task cancellation: {e}\")
    else:
        logger.info(\"No lingering background tasks found.\")
    logger.info(\"--- Application shutdown complete. ---\")

# FastAPI App Creation
app = FastAPI(
    title=\"FoSBot (Whatnot + YouTube + Twitch + X)\",
    version=\"0.7.3\",
    lifespan=lifespan
)

# Serve whatnot_extension.zip from project root
@app.get(\"/whatnot_extension.zip\")
async def serve_whatnot_extension():
    zip_path = Path(\"whatnot_extension.zip\")
    if not zip_path.is_file():
        zip_path = Path(\"static/whatnot_extension.zip\")
        if not zip_path.is_file():
            raise HTTPException(status_code=404, detail=\"Whatnot extension ZIP file not found\")
    return FileResponse(zip_path, media_type=\"application/zip\", filename=\"whatnot_extension.zip\")

# Mount Routers
app.include_router(auth_api.router)
app.include_router(ws_endpoints.router, prefix=\"/ws\")
app.include_router(settings_api.router, prefix=\"/api\", tags=[\"Settings & Control\"])
app.include_router(commands_api.router, prefix=\"/api\", tags=[\"Commands\"])

# Mount Static Files
STATIC_DIR = \"static\"
static_path = Path(STATIC_DIR)
if not static_path.is_dir():
    logger.error(f\"Static files directory '{STATIC_DIR}' not found at {static_path.resolve()}. Dashboard UI unavailable.\")
else:
    try:
        app.mount(\"/\", StaticFiles(directory=STATIC_DIR, html=True), name=\"static\")
        logger.info(f\"Mounted static files for dashboard UI from './{STATIC_DIR}'.\")
    except Exception as e:
        logger.exception(f\"Failed to mount static files directory './{STATIC_DIR}': {e}\")

# Direct Run (Debugging Only)
if __name__ == \"__main__\":
    import uvicorn
    logger.warning(\"Running via main.py is intended for debugging ONLY. Use 'uvicorn app.main:app --reload'.\")
    uvicorn.run(\"app.main:app\", host=settings['WS_HOST'], port=settings['WS_PORT'], log_level=settings['LOG_LEVEL'].lower(), reload=True)
"

write_file "$PROJECT_DIR/app/events.py" "# Version History: 0.7.2 -> 0.7.3
from dataclasses import dataclass
from datetime import datetime

@dataclass
class InternalChatMessage:
    platform: str
    channel: str
    user: str
    text: str
    timestamp: str

@dataclass
class ChatMessageReceived:
    message: InternalChatMessage

@dataclass
class PlatformStatusUpdate:
    platform: str
    status: str
    message: str = \"\"

@dataclass
class ServiceControl:
    service_name: str
    command: str

@dataclass
class SettingsUpdated:
    keys_updated: list
"

# app/core/ Directory Files
write_file "$PROJECT_DIR/app/core/__init__.py" "# Version History: 0.7.2 -> 0.7.3
# Empty file to make core a package"

write_file "$PROJECT_DIR/app/core/config.py" "# Version History: 0.7.2 -> 0.7.3
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
import json

# Setup logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# Load .env file
env_path = Path('.') / '.env'
if env_path.is_file():
    load_dotenv(dotenv_path=env_path)
    logger.info(f\"Loaded .env config from: {env_path}\")
else:
    logger.warning(f\"No .env file found at {env_path}\")

# Initialize settings dictionary
settings = {
    'COMMAND_PREFIX': os.getenv('COMMAND_PREFIX', '!'),
    'WS_HOST': os.getenv('WS_HOST', 'localhost'),
    'WS_PORT': int(os.getenv('WS_PORT', 8000)),
    'LOG_LEVEL': os.getenv('LOG_LEVEL', 'DEBUG'),
    'DATA_DIR': os.getenv('DATA_DIR', 'data'),
    'TWITCH_CHANNELS': os.getenv('TWITCH_CHANNELS', ''),
    'twitch_access_token': os.getenv('TWITCH_ACCESS_TOKEN', ''),
    'youtube_api_key': os.getenv('YOUTUBE_API_KEY', ''),
    'x_api_key': os.getenv('X_API_KEY', ''),
    'x_api_secret': os.getenv('X_API_SECRET', ''),
    'x_access_token': os.getenv('X_ACCESS_TOKEN', ''),
    'x_access_token_secret': os.getenv('X_ACCESS_TOKEN_SECRET', '')
}

# Load settings from settings.json
settings_file = Path(settings['DATA_DIR']) / 'settings.json'
if settings_file.is_file():
    try:
        with settings_file.open('r') as f:
            file_settings = json.load(f)
            settings.update(file_settings)
            logger.info(f\"Loaded settings from {settings_file}\")
    except Exception as e:
        logger.error(f\"Error loading settings from {settings_file}: {e}\")
else:
    logger.warning(f\"No settings.json found at {settings_file}\")

# Create data directory if it doesn't exist
data_dir = Path(settings['DATA_DIR'])
if not data_dir.is_dir():
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f\"Data directory verified/created: {data_dir}\")
else:
    logger.info(f\"Data directory exists: {data_dir}\")

# Save settings to settings.json
try:
    with settings_file.open('w') as f:
        json.dump(settings, f, indent=2)
    logger.debug(f\"Saved settings to {settings_file}\")
except Exception as e:
    logger.error(f\"Error saving settings to {settings_file}: {e}\")
"

write_file "$PROJECT_DIR/app/core/event_bus.py" "# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
from typing import Any, Callable, Type, Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._handlers: Dict[Type[Any], List[Callable[[Any], None]]] = defaultdict(list)
        self._queue = asyncio.Queue()
        self._running = False
        self._task = None

    def subscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        \"\"\"Subscribe a handler to an event type.\"\"\"
        self._handlers[event_type].append(handler)
        logger.debug(f\"Handler '{handler.__name__}' subscribed to {event_type.__name__}\")

    def unsubscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        \"\"\"Unsubscribe a handler from an event type.\"\"\"
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f\"Handler '{handler.__name__}' unsubscribed from {event_type.__name__}\")

    def publish(self, event: Any) -> None:
        \"\"\"Publish an event to the queue.\"\"\"
        self._queue.put_nowait(event)
        logger.debug(f\"Event {type(event).__name__} published (qsize: {self._queue.qsize()}).\")

    async def start(self):
        \"\"\"Start the event bus processor.\"\"\"
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._process_events(), name=\"EventBusProcessor\")
            logger.info(\"Event bus processor task started.\")

    async def stop(self):
        \"\"\"Stop the event bus processor.\"\"\"
        if self._running:
            self._running = False
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                    logger.info(\"Event bus processor task stopped.\")
                except asyncio.CancelledError:
                    logger.info(\"Event bus processing task cancelled.\")
            self._task = None

    async def _process_events(self):
        \"\"\"Process events from the queue.\"\"\"
        logger.info(\"Event bus started.\")
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                logger.debug(f\"Processing event {type(event).__name__} from queue (qsize: {self._queue.qsize()}).\")
                for event_type in self._handlers:
                    if isinstance(event, event_type):
                        for handler in self._handlers[event_type]:
                            try:
                                await handler(event)
                                logger.debug(f\"Handler '{handler.__name__}' processed {type(event).__name__}\")
                            except Exception as e:
                                logger.error(f\"Error in handler '{handler.__name__}' for {type(event).__name__}: {e}\", exc_info=True)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info(\"Event bus processing task cancelled.\")
                break
            except Exception as e:
                logger.error(f\"Error processing event: {e}\", exc_info=True)

event_bus = EventBus()
"

write_file "$PROJECT_DIR/app/core/json_store.py" "# Version History: 0.7.2 -> 0.7.3
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict
import aiofiles

logger = logging.getLogger(__name__)

async def load_json_data(file_path: Path) -> Dict[str, Any]:
    \"\"\"Load JSON data from a file with async file locking.\"\"\"
    try:
        async with aiofiles.open(file_path, mode='r') as f:
            content = await f.read()
        return json.loads(content) if content else {}
    except FileNotFoundError:
        logger.warning(f\"JSON file not found, creating new: {file_path}\")
        return {}
    except json.JSONDecodeError:
        logger.error(f\"Invalid JSON in {file_path}, returning empty dict\")
        return {}
    except Exception as e:
        logger.error(f\"Error loading JSON from {file_path}: {e}\")
        return {}

async def save_json_data(file_path: Path, data: Dict[str, Any]) -> None:
    \"\"\"Save JSON data to a file with async file locking.\"\"\"
    try:
        os.makedirs(file_path.parent, exist_ok=True)
        async with aiofiles.open(file_path, mode='w') as f:
            await f.write(json.dumps(data, indent=2))
        logger.debug(f\"Saved JSON to {file_path}\")
    except Exception as e:
        logger.error(f\"Error saving JSON to {file_path}: {e}\")
"

# app/apis/ Directory Files
write_file "$PROJECT_DIR/app/apis/__init__.py" "# Version History: 0.7.2 -> 0.7.3
# Empty file to make apis a package"

write_file "$PROJECT_DIR/app/apis/auth_api.py" "# Version History: 0.7.2 -> 0.7.3
from fastapi import APIRouter, HTTPException
from app.core.config import logger

router = APIRouter()

@router.get(\"/auth/login/{platform}\")
async def login_platform(platform: str):
    logger.info(f\"Login requested for platform: {platform}\")
    raise HTTPException(status_code=501, detail=\"Not implemented\")
"

write_file "$PROJECT_DIR/app/apis/settings_api.py" "# Version History: 0.7.2 -> 0.7.3
from fastapi import APIRouter, HTTPException
from app.core.config import logger, settings
from app.core.json_store import load_json_data, save_json_data
from app.events import SettingsUpdated
from app.core.event_bus import event_bus
from pydantic import BaseModel
from pathlib import Path

router = APIRouter()

class AllSettingsModel(BaseModel):
    COMMAND_PREFIX: str
    LOG_LEVEL: str
    TWITCH_CHANNELS: str
    twitch_access_token: str
    youtube_api_key: str
    x_api_key: str
    x_api_secret: str
    x_access_token: str
    x_access_token_secret: str

@router.get(\"/settings\")
async def get_settings():
    logger.debug(\"Returning settings\")
    return settings

@router.post(\"/settings\")
async def update_settings(new_settings: AllSettingsModel):
    logger.info(\"Received settings update request\")
    settings_file = Path(settings['DATA_DIR']) / 'settings.json'
    current_settings = await load_json_data(settings_file)
    updated = False

    for key, value in new_settings.dict().items():
        if current_settings.get(key) != value:
            current_settings[key] = value
            settings[key] = value  # Update in-memory settings
            updated = True

    if updated:
        await save_json_data(settings_file, current_settings)
        event_bus.publish(SettingsUpdated(keys_updated=list(new_settings.dict().keys())))
        logger.info(\"Settings updated and event published\")
    return {\"status\": \"success\"}

@router.post(\"/control/{service}/{command}\")
async def control_service(service: str, command: str):
    logger.info(f\"Received control request: {command} for {service}\")
    if service not in ['twitch', 'youtube', 'x', 'whatnot']:
        raise HTTPException(status_code=400, detail=\"Invalid service\")
    if command not in [\"start\", \"stop\", \"restart\"]:
        raise HTTPException(status_code=400, detail=\"Invalid command\")
    event_bus.publish(ServiceControl(service_name=service, command=command))
    return {\"status\": \"success\"}
"

write_file "$PROJECT_DIR/app/apis/ws_endpoints.py" "# Version History: 0.7.2 -> 0.7.3
from fastapi import WebSocket, APIRouter
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate
from app.services.dashboard_service import ConnectionManager
from app.core.config import logger
from datetime import datetime

router = APIRouter()
manager = ConnectionManager()

@router.websocket(\"/dashboard\")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        async def send_status(event: PlatformStatusUpdate):
            await websocket.send_json({
                'type': 'status_update',
                'payload': {
                    'platform': event.platform,
                    'status': event.status,
                    'message': event.message
                }
            })

        event_bus.subscribe(PlatformStatusUpdate, send_status)
        while True:
            await websocket.receive_json()
    except Exception as e:
        logger.error(f\"Dashboard WebSocket error: {e}\")
    finally:
        event_bus.unsubscribe(PlatformStatusUpdate, send_status)
        await manager.disconnect(websocket)

@router.websocket(\"/whatnot\")
async def whatnot_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        async def send_message(event: ChatMessageReceived):
            if event.message.platform == 'whatnot':
                await websocket.send_json({
                    'type': 'chat_message',
                    'payload': {
                        'username': event.message.user,
                        'message': event.message.text,
                        'platform': event.message.platform
                    }
                })

        event_bus.subscribe(ChatMessageReceived, send_message)
        while True:
            data = await websocket.receive_json()
            logger.debug(f\"Received Whatnot WebSocket message: {data}\")
            if data.get('type') == 'chat_message':
                event_bus.publish(ChatMessageReceived(
                    message=InternalChatMessage(
                        platform='whatnot',
                        channel='unknown',
                        user=data['payload']['username'],
                        text=data['payload']['message'],
                        timestamp=datetime.now().isoformat()
                    )
                ))
            elif data.get('type') == 'queryStatus':
                await websocket.send_json({'type': 'pong'})
            elif data.get('type') == 'debug':
                logger.debug(f\"Extension debug: {data.get('message')}\")
    except Exception as e:
        logger.error(f\"Whatnot WebSocket error: {e}\")
    finally:
        event_bus.unsubscribe(ChatMessageReceived, send_message)
        await websocket.close()

@router.websocket(\"/debug\")
async def debug_websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            if data.get('type') == 'debug':
                logger.debug(f\"Extension debug: {data.get('message')}\")
    except Exception as e:
        logger.error(f\"Debug WebSocket error: {e}\")
    finally:
        await websocket.close()
"

write_file "$PROJECT_DIR/app/apis/commands_api.py" "# Version History: 0.7.2 -> 0.7.3
from fastapi import APIRouter
from app.core.config import logger, settings
from app.core.json_store import load_json_data, save_json_data
from pathlib import Path

router = APIRouter()

@router.get(\"/commands\")
async def get_commands():
    logger.debug(\"Fetching all commands\")
    commands_file = Path(settings['DATA_DIR']) / 'commands.json'
    commands = await load_json_data(commands_file)
    logger.debug(f\"Retrieved commands: {commands}\")
    return commands

@router.post(\"/commands/{command}\")
async def add_command(command: str, response: str):
    logger.info(f\"Adding command: !{command} with response: {response}\")
    commands_file = Path(settings['DATA_DIR']) / 'commands.json'
    commands = await load_json_data(commands_file)
    commands[command] = response
    await save_json_data(commands_file, commands)
    return {\"status\": \"success\"}
"

# app/services/ Directory Files
write_file "$PROJECT_DIR/app/services/__init__.py" "# Version History: 0.7.2 -> 0.7.3
# Empty file to make services a package"

write_file "$PROJECT_DIR/app/services/chat_processor.py" "# Version History: 0.7.2 -> 0.7.3
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
    logger.info(\"Setting up chat processor...\")
    event_bus.subscribe(ChatMessageReceived, handle_chat_message)
    logger.info(\"Chat processor set up\")
"

write_file "$PROJECT_DIR/app/services/dashboard_service.py" "# Version History: 0.7.2 -> 0.7.3
import logging
from fastapi import WebSocket
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate, LogMessage, BotResponseToSend, BroadcastStreamerMessage
from app.core.config import logger

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(\"Dashboard WebSocket client connected\")

    async def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
        logger.info(\"Dashboard WebSocket client disconnected\")

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f\"Error broadcasting to dashboard client: {e}\")

manager = ConnectionManager()

async def handle_chat_message(event: ChatMessageReceived):
    await manager.broadcast({
        'type': 'chat_message',
        'payload': {
            'platform': event.message.platform,
            'channel': event.message.channel,
            'user': event.message.user,
            'text': event.message.text,
            'timestamp': event.message.timestamp
        }
    })

async def handle_status_update(event: PlatformStatusUpdate):
    await manager.broadcast({
        'type': 'status_update',
        'payload': {
            'platform': event.platform,
            'status': event.status,
            'message': event.message
        }
    })

async def handle_log_message(event: LogMessage):
    await manager.broadcast({
        'type': 'log_message',
        'payload': {
            'level': event.level,
            'message': event.message
        }
    })

async def handle_bot_response(event: BotResponseToSend):
    await manager.broadcast({
        'type': 'bot_response',
        'payload': {
            'platform': event.platform,
            'channel': event.channel,
            'message': event.message
        }
    })

async def handle_broadcast_message(event: BroadcastStreamerMessage):
    await manager.broadcast({
        'type': 'streamer_message',
        'payload': {
            'platform': event.platform,
            'channel': event.channel,
            'message': event.message
        }
    })

def setup_dashboard_service_listeners():
    logger.info(\"Setting up dashboard service listeners...\")
    event_bus.subscribe(ChatMessageReceived, handle_chat_message)
    event_bus.subscribe(PlatformStatusUpdate, handle_status_update)
    event_bus.subscribe(LogMessage, handle_log_message)
    event_bus.subscribe(BotResponseToSend, handle_bot_response)
    event_bus.subscribe(BroadcastStreamerMessage, handle_broadcast_message)
"

write_file "$PROJECT_DIR/app/services/streamer_command_handler.py" "# Version History: 0.7.2 -> 0.7.3
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
    logger.info(f\"Service control command received: {event.command} for {event.service_name}\")

def setup_streamer_command_handler():
    logger.info(\"Setting up streamer command handler...\")
    event_bus.subscribe(CommandDetected, handle_streamer_command)
    event_bus.subscribe(ServiceControl, handle_service_control)
"

write_file "$PROJECT_DIR/app/services/twitch_service.py" "# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
from typing import Optional
from twitchio.ext import commands
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global state
_STATE = {\"running\": False, \"bot\": None, \"task\": None}

class TwitchBot(commands.Bot):
    def __init__(self):
        super().__init__(
            token=settings.get('twitch_access_token', ''),
            prefix=settings.get('COMMAND_PREFIX', '!'),
            initial_channels=[ch.strip() for ch in settings.get('TWITCH_CHANNELS', '').split(',') if ch.strip()]
        )

    async def event_ready(self):
        logger.info(\"Twitch bot connected and ready.\")
        event_bus.publish(PlatformStatusUpdate(platform='twitch', status='connected'))

    async def event_message(self, message):
        if message.author is None:
            return
        logger.debug(f\"Twitch message received: {message.author.name}: {message.content}\")
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
        logger.debug(f\"Twitch ping command executed by {ctx.author.name}\")

async def run_twitch_bot():
    \"\"\"Main runner for Twitch bot service.\"\"\"
    logger.info(\"Twitch bot runner started.\")
    if not settings.get('twitch_access_token') or not settings.get('TWITCH_CHANNELS'):
        logger.error(\"Missing Twitch configuration: access token or channels not set.\")
        event_bus.publish(PlatformStatusUpdate(
            platform='twitch',
            status='disabled',
            message=\"Missing access token or channels\"
        ))
        return

    _STATE[\"bot\"] = TwitchBot()
    _STATE[\"running\"] = True
    while _STATE[\"running\"]:
        try:
            await _STATE[\"bot\"].start()
        except Exception as e:
            logger.error(f\"Twitch bot failed: {e}\", exc_info=True)
            event_bus.publish(PlatformStatusUpdate(
                platform='twitch',
                status='error',
                message=str(e)
            ))
            if _STATE[\"running\"]:
                await asyncio.sleep(10)

async def stop_twitch_bot():
    \"\"\"Stops the Twitch bot service gracefully.\"\"\"
    logger.info(\"Stop requested for Twitch bot.\")
    _STATE[\"running\"] = False
    if _STATE[\"bot\"]:
        try:
            await _STATE[\"bot\"].close()
            logger.info(\"Twitch bot stopped successfully.\")
        except Exception as e:
            logger.error(f\"Error stopping Twitch bot: {e}\")
    if _STATE.get(\"task\") and not _STATE[\"task\"].done():
        logger.info(\"Cancelling Twitch bot task...\")
        _STATE[\"task\"].cancel()
        try:
            await _STATE[\"task\"]
        except asyncio.CancelledError:
            logger.info(\"Twitch bot task cancellation confirmed.\")
    _STATE[\"task\"] = None
    event_bus.publish(PlatformStatusUpdate(platform='twitch', status='stopped'))

def start_twitch_service_task() -> Optional[asyncio.Task]:
    \"\"\"Creates and returns a task for running the Twitch bot.\"\"\"
    global _STATE
    if _STATE.get(\"task\") and not _STATE[\"task\"].done():
        logger.warning(\"Twitch bot task already running.\")
        return _STATE[\"task\"]
    logger.info(\"Creating background task for Twitch service if configured.\")
    if settings.get('twitch_access_token') and settings.get('TWITCH_CHANNELS'):
        _STATE[\"task\"] = asyncio.create_task(run_twitch_bot(), name=\"TwitchBotRunner\")
        return _STATE[\"task\"]
    else:
        logger.warning(\"Twitch service not started due to missing configuration.\")
        event_bus.publish(PlatformStatusUpdate(platform='twitch', status='disabled', message=\"Missing configuration\"))
        return None
"

write_file "$PROJECT_DIR/app/services/youtube_service.py" "# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global state
_STATE = {\"running\": False, \"task\": None}

async def run_youtube_service():
    \"\"\"Main runner for YouTube live chat service.\"\"\"
    logger.info(\"YouTube service runner started.\")
    youtube = None
    try:
        youtube = build('youtube', 'v3', developerKey=settings.get('youtube_api_key'))
        logger.debug(\"YouTube API client initialized\")
    except Exception as e:
        logger.error(f\"Failed to initialize YouTube API client: {e}\")
        event_bus.publish(PlatformStatusUpdate(
            platform='youtube',
            status='disabled',
            message=\"Failed to initialize API client\"
        ))
        return

    _STATE[\"running\"] = True
    while _STATE[\"running\"]:
        try:
            # Find active live broadcast
            request = youtube.liveBroadcasts().list(
                part=\"id,snippet\",
                broadcastStatus=\"active\",
                maxResults=1
            )
            response = await asyncio.get_event_loop().run_in_executor(None, request.execute)
            if not response.get('items'):
                logger.warning(\"No active YouTube live broadcasts found.\")
                event_bus.publish(PlatformStatusUpdate(
                    platform='youtube',
                    status='waiting',
                    message=\"No active live broadcasts\"
                ))
                await asyncio.sleep(60)
                continue

            live_broadcast = response['items'][0]
            live_chat_id = live_broadcast['snippet']['liveChatId']
            logger.info(f\"Found active live chat: {live_chat_id}\")
            event_bus.publish(PlatformStatusUpdate(platform='youtube', status='connected'))

            # Poll live chat messages
            next_page_token = None
            while _STATE[\"running\"]:
                request = youtube.liveChatMessages().list(
                    liveChatId=live_chat_id,
                    part=\"snippet,authorDetails\",
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
                    logger.debug(f\"YouTube message: {author.get('displayName')}: {snippet.get('displayMessage')}\")
                next_page_token = response.get('nextPageToken')
                polling_interval = response.get('pollingIntervalMillis', 5000) / 1000
                await asyncio.sleep(polling_interval)
        except HttpError as e:
            logger.error(f\"YouTube API error: {e}\")
            event_bus.publish(PlatformStatusUpdate(
                platform='youtube',
                status='error',
                message=str(e)
            ))
            await asyncio.sleep(10)
        except Exception as e:
            logger.error(f\"YouTube service error: {e}\", exc_info=True)
            event_bus.publish(PlatformStatusUpdate(
                platform='youtube',
                status='error',
                message=str(e)
            ))
            await asyncio.sleep(10)

async def stop_youtube_service():
    \"\"\"Stops the YouTube service gracefully.\"\"\"
    logger.info(\"Stop requested for YouTube service.\")
    _STATE[\"running\"] = False
    if _STATE.get(\"task\") and not _STATE[\"task\"].done():
        logger.info(\"Cancelling YouTube service task...\")
        _STATE[\"task\"].cancel()
        try:
            await _STATE[\"task\"]
        except asyncio.CancelledError:
            logger.info(\"YouTube service task cancellation confirmed.\")
    _STATE[\"task\"] = None
    event_bus.publish(PlatformStatusUpdate(platform='youtube', status='stopped'))

def start_youtube_service_task() -> asyncio.Task | None:
    \"\"\"Creates and returns a task for running the YouTube service.\"\"\"
    global _STATE
    if _STATE.get(\"task\") and not _STATE[\"task\"].done():
        logger.warning(\"YouTube service task already running.\")
        return _STATE[\"task\"]
    logger.info(\"Creating background task for YouTube service if configured.\")
    if settings.get('youtube_api_key'):
        _STATE[\"task\"] = asyncio.create_task(run_youtube_service(), name=\"YouTubeServiceRunner\")
        return _STATE[\"task\"]
    else:
        logger.warning(\"YouTube service not started due to missing API key.\")
        event_bus.publish(PlatformStatusUpdate(platform='youtube', status='disabled', message=\"Missing API key\"))
        return None
"

write_file "$PROJECT_DIR/app/services/x_service.py" "# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
import tweepy
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)

# Global state
_STATE = {\"running\": False, \"task\": None}

async def run_x_service():
    \"\"\"Main runner for X (Twitter) service to monitor mentions.\"\"\"
    logger.info(\"X service runner started.\")
    if not all([
        settings.get('x_api_key'),
        settings.get('x_api_secret'),
        settings.get('x_access_token'),
        settings.get('x_access_token_secret')
    ]):
        logger.error(\"Missing X configuration: API credentials not set.\")
        event_bus.publish(PlatformStatusUpdate(
            platform='x',
            status='disabled',
            message=\"Missing API credentials\"
        ))
        return

    try:
        client = tweepy.Client(
            consumer_key=settings['x_api_key'],
            consumer_secret=settings['x_api_secret'],
            access_token=settings['x_access_token'],
            access_token_secret=settings['x_access_token_secret']
        )
        logger.debug(\"Tweepy client initialized\")
    except Exception as e:
        logger.error(f\"Failed to initialize Tweepy client: {e}\")
        event_bus.publish(PlatformStatusUpdate(
            platform='x',
            status='disabled',
            message=\"Failed to initialize client\"
        ))
        return

    _STATE[\"running\"] = True
    since_id = None
    while _STATE[\"running\"]:
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
                    logger.debug(f\"X mention received: {author}: {tweet.text}\")
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
            logger.error(f\"X service error: {e}\", exc_info=True)
            event_bus.publish(PlatformStatusUpdate(
                platform='x',
                status='error',
                message=str(e)
            ))
            await asyncio.sleep(10)

async def stop_x_service():
    \"\"\"Stops the X service gracefully.\"\"\"
    logger.info(\"Stop requested for X service.\")
    _STATE[\"running\"] = False
    if _STATE.get(\"task\") and not _STATE[\"task\"].done():
        logger.info(\"Cancelling X service task...\")
        _STATE[\"task\"].cancel()
        try:
            await _STATE[\"task\"]
        except asyncio.CancelledError:
            logger.info(\"X service task cancellation confirmed.\")
    _STATE[\"task\"] = None
    event_bus.publish(PlatformStatusUpdate(platform='x', status='stopped'))

def start_x_service_task() -> asyncio.Task | None:
    \"\"\"Creates and returns a task for running the X service.\"\"\"
    global _STATE
    if _STATE.get(\"task\") and not _STATE[\"task\"].done():
        logger.warning(\"X service task already running.\")
        return _STATE[\"task\"]
    logger.info(\"Creating background task for X service if configured.\")
    if all([
        settings.get('x_api_key'),
        settings.get('x_api_secret'),
        settings.get('x_access_token'),
        settings.get('x_access_token_secret')
    ]):
        _STATE[\"task\"] = asyncio.create_task(run_x_service(), name=\"XServiceRunner\")
        return _STATE[\"task\"]
    else:
        logger.warning(\"X service not started due to missing configuration.\")
        event_bus.publish(PlatformStatusUpdate(platform='x', status='disabled', message=\"Missing configuration\"))
        return None
"

write_file "$PROJECT_DIR/app/services/whatnot_bridge.py" "# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
import websockets
from fastapi import WebSocket
from app.core.event_bus import event_bus
from app.events import ChatMessageReceived, PlatformStatusUpdate, ServiceControl, SettingsUpdated
from app.core.config import settings
from datetime import datetime

logger = logging.getLogger(__name__)

# Global state
_STATE = {\"running\": False, \"task\": None}
_websockets: set[WebSocket] = set()

async def run_whatnot_bridge():
    \"\"\"Main runner for Whatnot bridge service.\"\"\"
    logger.info(\"Whatnot bridge runner started.\")
    WS_HOST = settings.get('WS_HOST', 'localhost')
    WS_PORT = settings.get('WS_PORT', 8000)
    if not WS_HOST or not WS_PORT:
        logger.error(\"Missing WebSocket configuration: WS_HOST or WS_PORT not set.\")
        event_bus.publish(PlatformStatusUpdate(
            platform='whatnot',
            status='disabled',
            message=\"Missing WebSocket host or port\"
        ))
        return

    _STATE[\"running\"] = True
    while _STATE[\"running\"]:
        try:
            async with websockets.serve(handle_websocket, WS_HOST, WS_PORT, ping_interval=30, ping_timeout=30):
                logger.info(f\"Whatnot WebSocket server running on ws://{WS_HOST}:{WS_PORT}/ws/whatnot\")
                event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='connected'))
                await asyncio.Future()  # Run until cancelled
        except Exception as e:
            logger.error(f\"Whatnot WebSocket server failed: {e}\", exc_info=True)
            event_bus.publish(PlatformStatusUpdate(
                platform='whatnot',
                status='error',
                message=str(e)
            ))
            if _STATE[\"running\"]:
                await asyncio.sleep(10)

async def handle_websocket(websocket: WebSocket):
    \"\"\"Handles WebSocket connections for Whatnot bridge.\"\"\"
    try:
        await websocket.accept()
        _websockets.add(websocket)
        logger.info(\"Whatnot WebSocket client connected\")
        async def send_message(event: ChatMessageReceived):
            if event.message.platform == 'whatnot':
                try:
                    await websocket.send_json({
                        'type': 'chat_message',
                        'payload': {
                            'username': event.message.user,
                            'message': event.message.text,
                            'platform': event.message.platform
                        }
                    })
                    logger.debug(f\"Sent Whatnot message to client: {event.message.text}\")
                except Exception as e:
                    logger.error(f\"Error sending message to Whatnot client: {e}\")

        event_bus.subscribe(ChatMessageReceived, send_message)
        try:
            while True:
                data = await websocket.receive_json()
                logger.debug(f\"Received Whatnot WebSocket message: {data}\")
                if data.get('type') == 'chat_message':
                    event_bus.publish(ChatMessageReceived(
                        message=InternalChatMessage(
                            platform='whatnot',
                            channel='unknown',
                            user=data['payload']['username'],
                            text=data['payload']['message'],
                            timestamp=datetime.now().isoformat()
                        )
                    ))
                elif data.get('type') == 'queryStatus':
                    await websocket.send_json({'type': 'pong'})
                elif data.get('type') == 'debug':
                    logger.debug(f\"Extension debug: {data.get('message')}\")
        except websockets.exceptions.ConnectionClosed:
            logger.info(\"Whatnot WebSocket client disconnected\")
        finally:
            event_bus.unsubscribe(ChatMessageReceived, send_message)
            _websockets.remove(websocket)
    except Exception as e:
        logger.error(f\"Whatnot WebSocket handler error: {e}\", exc_info=True)

async def stop_whatnot_bridge():
    \"\"\"Stops the Whatnot bridge service gracefully.\"\"\"
    logger.info(\"Stop requested for Whatnot bridge.\")
    _STATE[\"running\"] = False
    for websocket in list(_websockets):
        try:
            await websocket.close()
            _websockets.remove(websocket)
        except Exception as e:
            logger.error(f\"Error closing Whatnot WebSocket: {e}\")
    if _STATE.get(\"task\") and not _STATE[\"task\"].done():
        logger.info(\"Cancelling Whatnot bridge task...\")
        _STATE[\"task\"].cancel()
        try:
            await _STATE[\"task\"]
        except asyncio.CancelledError:
            logger.info(\"Whatnot bridge task cancellation confirmed.\")
    _STATE[\"task\"] = None
    logger.info(\"Whatnot bridge stopped.\")
    event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='stopped'))

async def handle_settings_update(event: SettingsUpdated):
    \"\"\"Handles settings updates that affect Whatnot bridge.\"\"\"
    relevant_keys = {\"WS_HOST\", \"WS_PORT\"}
    if any(key in relevant_keys for key in event.keys_updated):
        logger.info(\"Whatnot-relevant settings updated, requesting service restart...\")
        event_bus.publish(ServiceControl(service_name=\"whatnot\", command=\"restart\"))

def start_whatnot_bridge_task() -> asyncio.Task | None:
    \"\"\"Creates and returns a task for running the Whatnot bridge.\"\"\"
    global _STATE
    if _STATE.get(\"task\") and not _STATE[\"task\"].done():
        logger.warning(\"Whatnot bridge task already running.\")
        return _STATE[\"task\"]
    logger.info(\"Creating background task for Whatnot bridge if WebSocket is configured.\")
    if settings.get('WS_HOST') and settings.get('WS_PORT'):
        _STATE[\"task\"] = asyncio.create_task(run_whatnot_bridge(), name=\"WhatnotBridgeRunner\")
        event_bus.subscribe(SettingsUpdated, handle_settings_update)
        return _STATE[\"task\"]
    else:
        logger.warning(\"Whatnot bridge not started due to missing WebSocket configuration.\")
        event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='disabled', message=\"Missing WebSocket configuration\"))
        return None
"

# static/ Directory Files
write_file "$PROJECT_DIR/static/index.html" "<!-- Version History: 0.7.2 -> 0.7.3 -->
<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>FoSBot Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 10px; background: #f0f0f0; }
        #header { background: #333; color: white; padding: 10px; text-align: center; }
        #tab-buttons { margin: 10px 0; }
        .tab-button { padding: 8px 16px; margin-right: 5px; background: #ddd; border: none; cursor: pointer; }
        .tab-button.active { background: #007bff; color: white; }
        #main-content { display: flex; }
        #content-area { flex: 3; background: white; padding: 15px; border-radius: 5px; }
        #sidebar { flex: 1; margin-left: 10px; background: #e9ecef; padding: 10px; border-radius: 5px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        #chat-output { max-height: 500px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }
        .chat-message { margin: 5px 0; }
        .chat-message-whatnot { color: #ff4500; }
        .chat-message-youtube { color: #ff0000; }
        .chat-message-twitch { color: #9146ff; }
        .chat-message-x { color: #1da1f2; }
        #streamer-input { width: 100%; padding: 5px; margin-top: 10px; }
        #sendButton, #clearButton { margin-top: 5px; padding: 5px 10px; }
        #status-indicators div { margin: 5px 0; }
        .status-light { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
        .status-light.connected { background: green; }
        .status-light.disconnected { background: red; }
        .status-light.error { background: orange; }
        .status-light.disabled { background: gray; }
        .settings-section { margin-bottom: 20px; }
        .settings-section h3 { margin-bottom: 10px; }
        .auth-status { display: inline-block; margin-right: 10px; }
        .control-button { margin: 5px; padding: 5px 10px; }
        .download-link { color: #007bff; text-decoration: underline; cursor: pointer; }
        .instructions { margin-top: 10px; font-size: 14px; }
        #commands-table { width: 100%; border-collapse: collapse; }
        #commands-table th, #commands-table td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        #commands-table th { background: #f4f4f4; }
        .command-action { cursor: pointer; color: #007bff; }
        #add-command-form { margin-top: 10px; }
        #add-command-form input { margin: 5px 0; padding: 5px; width: 100%; }
        #csv-upload { margin-top: 10px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
        .modal-content { background: white; margin: 15% auto; padding: 20px; width: 50%; border-radius: 5px; }
        .close { float: right; cursor: pointer; font-size: 20px; }
    </style>
</head>
<body>
    <div id=\"header\">
        <h1>FoSBot Dashboard</h1>
    </div>
    <div id=\"tab-buttons\">
        <button class=\"tab-button active\" data-tab=\"chat\">Chat</button>
        <button class=\"tab-button\" data-tab=\"commands\">Commands</button>
        <button class=\"tab-button\" data-tab=\"settings\">Settings</button>
    </div>
    <div id=\"main-content\">
        <div id=\"content-area\">
            <!-- Chat Tab -->
            <div id=\"chat-container\" class=\"tab-content active\" data-tab-content=\"chat\">
                <h2>Live Chat</h2>
                <div id=\"chat-output\"></div>
                <input type=\"text\" id=\"streamerInput\" placeholder=\"Type a message or command...\">
                <button id=\"sendButton\">Send</button>
                <button id=\"clearButton\">Clear Chat</button>
            </div>

            <!-- Commands Tab -->
            <div id=\"commands-container\" class=\"tab-content\" data-tab-content=\"commands\">
                <h2>Manage Commands</h2>
                <p>Create custom commands like <code>!roll</code> for your streams!</p>
                <table id=\"commands-table\">
                    <thead>
                        <tr>
                            <th>Command</th>
                            <th>Response</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
                <form id=\"add-command-form\">
                    <input type=\"text\" id=\"command-name\" placeholder=\"Command (e.g., roll)\" required>
                    <input type=\"text\" id=\"command-response\" placeholder=\"Response (e.g., Rolled a {user} d20!)\" required>
                    <button type=\"submit\">Add Command</button>
                </form>
                <div id=\"csv-upload\">
                    <label for=\"csv-file\">Upload CSV (format: command,response):</label>
                    <input type=\"file\" id=\"csv-file\" accept=\".csv\">
                </div>
            </div>

            <!-- Settings Tab -->
            <div id=\"settings-container\" class=\"tab-content\" data-tab-content=\"settings\">
                <h2>Application Settings</h2>
                <p id=\"settings-status\"></p>

                <!-- Whatnot Section -->
                <div class=\"settings-section\">
                    <h3>Whatnot Integration</h3>
                    <div id=\"whatnot-status-area\">
                        <span class=\"auth-status\">Status: Loading...</span>
                    </div>
                    <p>
                        <a href=\"/whatnot_extension.zip\" class=\"download-link\" download>Download Whatnot Extension</a>
                        <button class=\"control-button\" onclick=\"openWhatnotGuide()\">Guided Setup</button>
                    </p>
                    <div class=\"instructions\">
                        <strong>Quick Setup:</strong>
                        <p>Click \"Guided Setup\" for step-by-step help or download the extension and follow the README!</p>
                    </div>
                </div>

                <!-- YouTube Section -->
                <div class=\"settings-section\">
                    <h3>YouTube Authentication</h3>
                    <div id=\"youtube-auth-area\">
                        <span class=\"auth-status\">Loading...</span>
                        <button class=\"control-button\" data-platform=\"youtube\" data-action=\"login\">Login</button>
                        <button class=\"control-button\" data-platform=\"youtube\" data-action=\"logout\" disabled>Logout</button>
                    </div>
                </div>

                <!-- Twitch Section -->
                <div class=\"settings-section\">
                    <h3>Twitch Authentication</h3>
                    <div id=\"twitch-auth-area\">
                        <span class=\"auth-status\">Loading...</span>
                        <button class=\"control-button\" data-platform=\"twitch\" data-action=\"login\">Login</button>
                        <button class=\"control-button\" data-platform=\"twitch\" data-action=\"logout\" disabled>Logout</button>
                    </div>
                </div>

                <!-- X Section -->
                <div class=\"settings-section\">
                    <h3>X Authentication</h3>
                    <div id=\"x-auth-area\">
                        <span class=\"auth-status\">Loading...</
                        <!-- Version History: 0.7.2 -> 0.7.3 -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FoSBot Dashboard</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 0; padding: 10px; background: #f0f0f0; }
        #header { background: #333; color: white; padding: 10px; text-align: center; }
        #tab-buttons { margin: 10px 0; }
        .tab-button { padding: 8px 16px; margin-right: 5px; background: #ddd; border: none; cursor: pointer; }
        .tab-button.active { background: #007bff; color: white; }
        #main-content { display: flex; }
        #content-area { flex: 3; background: white; padding: 15px; border-radius: 5px; }
        #sidebar { flex: 1; margin-left: 10px; background: #e9ecef; padding: 10px; border-radius: 5px; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
        #chat-output { max-height: 500px; overflow-y: auto; border: 1px solid #ccc; padding: 10px; }
        .chat-message { margin: 5px 0; }
        .chat-message-whatnot { color: #ff4500; }
        .chat-message-youtube { color: #ff0000; }
        .chat-message-twitch { color: #9146ff; }
        .chat-message-x { color: #1da1f2; }
        #streamer-input { width: 100%; padding: 5px; margin-top: 10px; }
        #sendButton, #clearButton { margin-top: 5px; padding: 5px 10px; }
        #status-indicators div { margin: 5px 0; }
        .status-light { display: inline-block; width: 10px; height: 10px; border-radius: 50%; margin-right: 5px; }
        .status-light.connected { background: green; }
        .status-light.disconnected { background: red; }
        .status-light.error { background: orange; }
        .status-light.disabled { background: gray; }
        .settings-section { margin-bottom: 20px; }
        .settings-section h3 { margin-bottom: 10px; }
        .auth-status { display: inline-block; margin-right: 10px; }
        .control-button { margin: 5px; padding: 5px 10px; }
        .download-link { color: #007bff; text-decoration: underline; cursor: pointer; }
        .instructions { margin-top: 10px; font-size: 14px; }
        #commands-table { width: 100%; border-collapse: collapse; }
        #commands-table th, #commands-table td { border: 1px solid #ccc; padding: 8px; text-align: left; }
        #commands-table th { background: #f4f4f4; }
        .command-action { cursor: pointer; color: #007bff; }
        #add-command-form { margin-top: 10px; }
        #add-command-form input { margin: 5px 0; padding: 5px; width: 100%; }
        #csv-upload { margin-top: 10px; }
        .modal { display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); }
        .modal-content { background: white; margin: 15% auto; padding: 20px; width: 50%; border-radius: 5px; }
        .close { float: right; cursor: pointer; font-size: 20px; }
    </style>
</head>
<body>
    <div id="header">
        <h1>FoSBot Dashboard</h1>
    </div>
    <div id="tab-buttons">
        <button class="tab-button active" data-tab="chat">Chat</button>
        <button class="tab-button" data-tab="commands">Commands</button>
        <button class="tab-button" data-tab="settings">Settings</button>
    </div>
    <div id="main-content">
        <div id="content-area">
            <!-- Chat Tab -->
            <div id="chat-container" class="tab-content active" data-tab-content="chat">
                <h2>Live Chat</h2>
                <div id="chat-output"></div>
                <input type="text" id="streamerInput" placeholder="Type a message or command...">
                <button id="sendButton">Send</button>
                <button id="clearButton">Clear Chat</button>
            </div>

            <!-- Commands Tab -->
            <div id="commands-container" class="tab-content" data-tab-content="commands">
                <h2>Manage Commands</h2>
                <p>Create custom commands like <code>!roll</code> for your streams!</p>
                <table id="commands-table">
                    <thead>
                        <tr>
                            <th>Command</th>
                            <th>Response</th>
                            <th>Actions</th>
                        </tr>
                    </thead>
                    <tbody></tbody>
                </table>
                <form id="add-command-form">
                    <input type="text" id="command-name" placeholder="Command (e.g., roll)" required>
                    <input type="text" id="command-response" placeholder="Response (e.g., Rolled a {user} d20!)" required>
                    <button type="submit">Add Command</button>
                </form>
                <div id="csv-upload">
                    <label for="csv-file">Upload CSV (format: command,response):</label>
                    <input type="file" id="csv-file" accept=".csv">
                </div>
            </div>

            <!-- Settings Tab -->
            <div id="settings-container" class="tab-content" data-tab-content="settings">
                <h2>Application Settings</h2>
                <p id="settings-status"></p>

                <!-- Whatnot Section -->
                <div class="settings-section">
                    <h3>Whatnot Integration</h3>
                    <div id="whatnot-status-area">
                        <span class="auth-status">Status: Loading...</span>
                    </div>
                    <p>
                        <a href="/whatnot_extension.zip" class="download-link" download>Download Whatnot Extension</a>
                        <button class="control-button" onclick="openWhatnotGuide()">Guided Setup</button>
                    </p>
                    <div class="instructions">
                        <strong>Quick Setup:</strong>
                        <p>Click "Guided Setup" for step-by-step help or download the extension and follow the README!</p>
                    </div>
                </div>

                <!-- YouTube Section -->
                <div class="settings-section">
                    <h3>YouTube Authentication</h3>
                    <div id="youtube-auth-area">
                        <span class="auth-status">Loading...</span>
                        <button class="control-button" data-platform="youtube" data-action="login">Login</button>
                        <button class="control-button" data-platform="youtube" data-action="logout" disabled>Logout</button>
                    </div>
                </div>

                <!-- Twitch Section -->
                <div class="settings-section">
                    <h3>Twitch Authentication</h3>
                    <div id="twitch-auth-area">
                        <span class="auth-status">Loading...</span>
                        <button class="control-button" data-platform="twitch" data-action="login">Login</button>
                        <button class="control-button" data-platform="twitch" data-action="logout" disabled>Logout</button>
                    </div>
                </div>

                <!-- X Section -->
                <div class="settings-section">
                    <h3>X Authentication</h3>
                    <div id="x-auth-area">
                        <span class="auth-status">Loading...</span>
                        <button class="control-button" data-platform="x" data-action="login">Login</button>
                        <button class="control-button" data-platform="x" data-action="logout" disabled>Logout</button>
                    </div>
                </div>

                <!-- App Config Section -->
                <div class="settings-section">
                    <h3>General Settings</h3>
                    <form id="app-settings-form">
                        <label>Command Prefix:</label><br>
                        <input type="text" name="COMMAND_PREFIX" maxlength="5" value="!"><br>
                        <label>Log Level:</label><br>
                        <select name="LOG_LEVEL">
                            <option value="DEBUG">DEBUG</option>
                            <option value="INFO">INFO</option>
                            <option value="WARNING">WARNING</option>
                            <option value="ERROR">ERROR</option>
                            <option value="CRITICAL">CRITICAL</option>
                        </select><br>
                        <label>Extra Twitch Channels (optional, comma-separated):</label><br>
                        <input type="text" name="TWITCH_CHANNELS" placeholder="channel1,channel2"><br>
                        <button type="submit">Save</button>
                    </form>
                </div>

                <!-- Service Control Section -->
                <div class="settings-section">
                    <h3>Service Control</h3>
                    <div>
                        <button class="control-button" data-service="whatnot" data-command="start">Start Whatnot</button>
                        <button class="control-button" data-service="whatnot" data-command="stop">Stop Whatnot</button>
                        <button class="control-button" data-service="whatnot" data-command="restart">Restart Whatnot</button>
                    </div>
                    <div>
                        <button class="control-button" data-service="youtube" data-command="start">Start YouTube</button>
                        <button class="control-button" data-service="youtube" data-command="stop">Stop YouTube</button>
                        <button class="control-button" data-service="youtube" data-command="restart">Restart YouTube</button>
                    </div>
                    <div>
                        <button class="control-button" data-service="twitch" data-command="start">Start Twitch</button>
                        <button class="control-button" data-service="twitch" data-command="stop">Stop Twitch</button>
                        <button class="control-button" data-service="twitch" data-command="restart">Restart Twitch</button>
                    </div>
                    <div>
                        <button class="control-button" data-service="x" data-command="start">Start X</button>
                        <button class="control-button" data-service="x" data-command="stop">Stop X</button>
                        <button class="control-button" data-service="x" data-command="restart">Restart X</button>
                    </div>
                </div>
            </div>
        </div>

        <!-- Sidebar -->
        <div id="sidebar">
            <h3>Status</h3>
            <div id="status-indicators">
                <div id="status-ws"><span class="status-light"></span><span class="status-text">WebSocket: Unknown</span></div>
                <div id="status-whatnot"><span class="status-light"></span><span class="status-text">Whatnot: Unknown</span></div>
                <div id="status-youtube"><span class="status-light"></span><span class="status-text">YouTube: Unknown</span></div>
                <div id="status-twitch"><span class="status-light"></span><span class="status-text">Twitch: Unknown</span></div>
                <div id="status-x"><span class="status-light"></span><span class="status-text">X: Unknown</span></div>
            </div>
            <h3>Logs</h3>
            <div id="log-output" style="max-height: 300px; overflow-y: auto; border: 1px solid #ccc; padding: 10px;"></div>
        </div>
    </div>

    <!-- Whatnot Setup Modal -->
    <div id="whatnot-guide-modal" class="modal">
        <div class="modal-content">
            <span class="close" onclick="closeWhatnotGuide()">×</span>
            <h3>Whatnot Extension Setup</h3>
            <ol>
                <li>Click <a href="/whatnot_extension.zip" download>"Download Whatnot Extension"</a> above.</li>
                <li>Unzip to a folder (e.g., <code>~/FoSBot_Whatnot</code>).</li>
                <li>In Chrome, go to <code>chrome://extensions/</code>, enable "Developer mode," click "Load unpacked," select the folder.</li>
                <li>On a Whatnot stream, click the extension icon, enable "Select Mode," click chat elements, save.</li>
            </ol>
            <p><strong>Watch:</strong> <a href="https://patreon.com/yourvideo" target="_blank">Setup Video</a></p>
            <button onclick="closeWhatnotGuide()">Close</button>
        </div>
    </div>

    <script src="main.js"></script>
</body>
</html>
"

write_file "$PROJECT_DIR/static/main.js" "// Version History: 0.7.2 -> 0.7.3
document.addEventListener('DOMContentLoaded', () => {
    const statusIndicators = {
        twitch: document.getElementById('status-twitch').querySelector('.status-light'),
        youtube: document.getElementById('status-youtube').querySelector('.status-light'),
        x: document.getElementById('status-x').querySelector('.status-light'),
        whatnot: document.getElementById('status-whatnot').querySelector('.status-light'),
        ws: document.getElementById('status-ws').querySelector('.status-light')
    };

    const statusTexts = {
        twitch: document.getElementById('status-twitch').querySelector('.status-text'),
        youtube: document.getElementById('status-youtube').querySelector('.status-text'),
        x: document.getElementById('status-x').querySelector('.status-text'),
        whatnot: document.getElementById('status-whatnot').querySelector('.status-text'),
        ws: document.getElementById('status-ws').querySelector('.status-text')
    };

    const ws = new WebSocket('ws://localhost:8000/ws/dashboard');
    ws.onopen = () => {
        console.log('Dashboard WebSocket connected');
        statusIndicators.ws.className = 'status-light connected';
        statusTexts.ws.textContent = 'WebSocket: Connected';
    };
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            if (data.type === 'status_update') {
                const { platform, status, message } = data.payload;
                const indicator = statusIndicators[platform];
                const text = statusTexts[platform];
                if (indicator && text) {
                    indicator.className = `status-light ${status}`;
                    text.textContent = `${platform.charAt(0).toUpperCase() + platform.slice(1)}: ${status.charAt(0).toUpperCase() + status.slice(1)}${message ? ' - ' + message : ''}`;
                    console.log(`Status update: ${platform} is ${status}${message ? ': ' + message : ''}`);
                }
            } else if (data.type === 'chat_message') {
                const { platform, user, text, timestamp } = data.payload;
                const chatOutput = document.getElementById('chat-output');
                const messageDiv = document.createElement('div');
                messageDiv.className = `chat-message chat-message-${platform}`;
                messageDiv.textContent = `[${platform}] ${user}: ${text} (${timestamp})`;
                chatOutput.appendChild(messageDiv);
                chatOutput.scrollTop = chatOutput.scrollHeight;
            }
        } catch (e) {
            console.error('Error parsing dashboard WebSocket message:', e);
        }
    };
    ws.onclose = () => {
        console.log('Dashboard WebSocket disconnected, retrying in 5s');
        statusIndicators.ws.className = 'status-light disconnected';
        statusTexts.ws.textContent = 'WebSocket: Disconnected';
        setTimeout(() => {
            location.reload();
        }, 5000);
    };

    // Tab navigation
    document.querySelectorAll('.tab-button').forEach(button => {
        button.addEventListener('click', () => {
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));
            button.classList.add('active');
            document.querySelector(`[data-tab-content="${button.dataset.tab}"]`).classList.add('active');
        });
    });

    // Service control buttons
    document.querySelectorAll('.control-button[data-service]').forEach(button => {
        button.addEventListener('click', () => {
            const service = button.dataset.service;
            const command = button.dataset.command;
            fetch(`/api/control/${service}/${command}`, { method: 'POST' })
                .then(res => res.json())
                .then(data => console.log(`${service} ${command}:`, data))
                .catch(err => console.error(`Control error for ${service} ${command}:`, err));
        });
    });

    // Clear chat button
    document.getElementById('clearButton').addEventListener('click', () => {
        document.getElementById('chat-output').innerHTML = '';
    });

    // Fetch initial commands
    fetch('/api/commands').then(res => res.json()).then(commands => {
        const tbody = document.getElementById('commands-table').querySelector('tbody');
        Object.entries(commands).forEach(([name, response]) => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>!${name}</td>
                <td>${response}</td>
                <td><span class="command-action">Delete</span></td>
            `;
            row.querySelector('.command-action').addEventListener('click', () => {
                // Implement delete functionality if needed
                console.log(`Delete command: ${name}`);
            });
            tbody.appendChild(row);
        });
    });
});
"

# whatnot_extension/ Directory Files
write_file "$PROJECT_DIR/whatnot_extension/manifest.json" "{
    \"manifest_version\": 3,
    \"name\": \"FoSBot Whatnot Helper\",
    \"version\": \"0.7.3\",
    \"description\": \"Connects Whatnot live streams to FoSBot\",
    \"permissions\": [
        \"storage\",
        \"activeTab\"
    ],
    \"background\": {
        \"service_worker\": \"background.js\"
    },
    \"content_scripts\": [
        {
            \"matches\": [\"https://*.whatnot.com/*\"],
            \"js\": [\"content.js\"]
        }
    ],
    \"action\": {
        \"default_popup\": \"popup.html\"
    }
}
"

write_file "$PROJECT_DIR/whatnot_extension/background.js" "// Version History: 0.7.2 -> 0.7.3
let ws = null;
let debugWs = null;

function connectWebSocket() {
    console.log('Attempting WebSocket connection to FoSBot');
    ws = new WebSocket('ws://localhost:8000/ws/whatnot');
    ws.onopen = () => {
        console.log('WebSocket connected to FoSBot');
        sendDebugLog('Background WebSocket connected to FoSBot');
        ws.send(JSON.stringify({ type: 'ping' }));
    };
    ws.onclose = () => {
        console.log('WebSocket disconnected, retrying in 5 seconds');
        sendDebugLog('Background WebSocket disconnected, retrying in 5s');
        setTimeout(connectWebSocket, 5000);
    };
    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        sendDebugLog(`Background WebSocket error: ${error}`);
    };
    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            console.log('Received message:', data);
            sendDebugLog(`Background received message: ${JSON.stringify(data)}`);
            if (data.type === 'pong') {
                console.log('Received pong from FoSBot');
                sendDebugLog('Background received pong from FoSBot');
            }
        } catch (e) {
            console.error('Error parsing WebSocket message:', e);
            sendDebugLog(`Background error parsing WebSocket message: ${e.message}`);
        }
    };
}

function initDebugWebSocket() {
    debugWs = new WebSocket('ws://localhost:8000/ws/debug');
    debugWs.onopen = () => {
        console.log('Background Debug WebSocket connected');
        sendDebugLog('Background Debug WebSocket connected');
    };
    debugWs.onclose = () => {
        console.log('Background Debug WebSocket disconnected, retrying in 5s');
        setTimeout(initDebugWebSocket, 5000);
    };
    debugWs.onerror = (error) => {
        console.error('Background Debug WebSocket error:', error);
    };
}
initDebugWebSocket();

function sendDebugLog(message) {
    if (debugWs && debugWs.readyState === WebSocket.OPEN) {
        debugWs.send(JSON.stringify({ type: 'debug', message }));
    }
}

connectWebSocket();

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    console.log('Background received message:', request);
    sendDebugLog(`Background received message: ${JSON.stringify(request)}`);
    if (request.type === 'chat_message' && ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
            type: 'chat_message',
            payload: request.payload
        }));
        sendResponse({ success: true });
        sendDebugLog('Background sent chat message to FoSBot');
    } else if (request.type === 'query_status') {
        sendResponse({
            wsConnected: ws && ws.readyState === WebSocket.OPEN,
            selectorsValid: true // Handled by content.js
        });
        sendDebugLog(`Background query status: wsConnected=${ws && ws.readyState === WebSocket.OPEN}`);
    } else {
        sendResponse({ success: false });
        sendDebugLog('Background message not handled');
    }
    return true; // Keep channel open
});
"

write_file "$PROJECT_DIR/whatnot_extension/popup.html" "<!DOCTYPE html>
<html>
<head>
    <title>FoSBot Whatnot Helper</title>
    <style>
        body { font-family: Arial, sans-serif; width: 350px; padding: 15px; }
        h3 { margin: 0 0 10px; }
        label { display: block; margin: 10px 0 5px; font-weight: bold; }
        input, button { width: 100%; padding: 8px; margin-bottom: 10px; box-sizing: border-box; }
        button { background: #007bff; color: white; border: none; cursor: pointer; }
        button:hover { background: #0056b3; }
        #status { font-size: 14px; margin: 10px 0; }
        #status.success { color: green; }
        #status.error { color: red; }
        #modeStatus { font-size: 16px; font-weight: bold; margin: 10px 0; }
        .instructions { font-size: 12px; margin-bottom: 10px; }
        .instructions ol { margin: 0; padding-left: 20px; }
        a { color: #007bff; text-decoration: none; }
        a:hover { text-decoration: underline; }
    </style>
</head>
<body>
    <h3>FoSBot Whatnot Helper</h3>
    <div id="modeStatus">Setup Mode: Checking...</div>
    <div id="status">Checking connection...</div>
    <label><input type="checkbox" id="setupMode"> Turn On Setup Mode</label>
    <div class="instructions">
        <p><strong>How to set up:</strong></p>
        <ol>
            <li>Start the FoSBot app in Terminal.</li>
            <li>Open a Whatnot stream page.</li>
            <li>Check "Turn On Setup Mode" above.</li>
            <li>Follow the box on the page to click chat parts.</li>
            <li>Click "Test Setup" when done.</li>
        </ol>
    </div>
    <button id="testButton">Test Setup</button>
    <p><a href="https://patreon.com/yourvideo" target="_blank">Watch Setup Video</a></p>
    <script src="popup.js"></script>
</body>
</html>
"

write_file "$PROJECT_DIR/whatnot_extension/popup.js" "// Version History: 0.7.2 -> 0.7.3
document.addEventListener('DOMContentLoaded', () => {
    console.log('Popup initialized');
    const setupModeCheckbox = document.getElementById('setupMode');
    const testButton = document.getElementById('testButton');
    const statusDiv = document.getElementById('status');
    const modeStatusDiv = document.getElementById('modeStatus');
    let ws = null;

    // Initialize WebSocket for debug logging
    function initDebugWebSocket() {
        ws = new WebSocket('ws://localhost:8000/ws/debug');
        ws.onopen = () => {
            console.log('Debug WebSocket connected');
            sendDebugLog('Popup WebSocket connected');
        };
        ws.onclose = () => {
            console.log('Debug WebSocket disconnected, retrying in 5s');
            setTimeout(initDebugWebSocket, 5000);
        };
        ws.onerror = (error) => {
            console.error('Debug WebSocket error:', error);
        };
    }
    initDebugWebSocket();

    function sendDebugLog(message) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify({ type: 'debug', message }));
        }
    }

    // Load saved settings
    chrome.storage.local.get(['setupMode'], (data) => {
        const isSetupMode = data.setupMode || false;
        setupModeCheckbox.checked = isSetupMode;
        updateModeStatus(isSetupMode);
        console.log('Loaded settings:', data);
        sendDebugLog(`Popup loaded settings: ${JSON.stringify(data)}`);
        updateConnectionStatus();
    });

    // Update setup mode status
    function updateModeStatus(isOn) {
        modeStatusDiv.textContent = `Setup Mode: ${isOn ? 'On' : 'Off'}`;
        modeStatusDiv.style.color = isOn ? 'green' : 'gray';
        sendDebugLog(`Setup mode updated: ${isOn ? 'On' : 'Off'}`);
    }

    // Update connection status
    function updateConnectionStatus() {
        chrome.runtime.sendMessage({ type: 'query_status' }, (response) => {
            if (chrome.runtime.lastError) {
                console.error('Status query error:', chrome.runtime.lastError);
                statusDiv.textContent = 'Error: Start the FoSBot app first!';
                statusDiv.className = 'error';
                sendDebugLog(`Status query error: ${chrome.runtime.lastError.message}`);
                setTimeout(updateConnectionStatus, 5000);
                return;
            }
            if (response && response.wsConnected) {
                statusDiv.textContent = 'Connected to FoSBot app';
                statusDiv.className = 'success';
                sendDebugLog('Connected to FoSBot app');
            } else {
                statusDiv.textContent = 'Start the FoSBot app and Whatnot service';
                statusDiv.className = 'error';
                sendDebugLog('Not connected to FoSBot app or Whatnot service');
            }
            setTimeout(updateConnectionStatus, 5000);
        });
    }

    // Toggle setup mode
    setupModeCheckbox.addEventListener('change', () => {
        const isChecked = setupModeCheckbox.checked;
        console.log('Setup Mode toggled:', isChecked);
        sendDebugLog(`Setup Mode toggled: ${isChecked}`);
        chrome.storage.local.set({ setupMode: isChecked }, () => {
            updateModeStatus(isChecked);
            chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
                if (tabs[0] && tabs[0].url.match(/^https:\/\/.*\.whatnot\.com\/.*/)) {
                    console.log('Sending toggle_setup_mode to tab:', tabs[0].id);
                    sendDebugLog(`Sending toggle_setup_mode to tab ${tabs[0].id}`);
                    chrome.tabs.sendMessage(tabs[0].id, {
                        type: 'toggle_setup_mode',
                        payload: { setupMode: isChecked }
                    }, (response) => {
                        if (chrome.runtime.lastError) {
                            console.error('Message error:', chrome.runtime.lastError);
                            statusDiv.textContent = 'Error: Ensure you are on a Whatnot stream page';
                            statusDiv.className = 'error';
                            sendDebugLog(`Message error: ${chrome.runtime.lastError.message}`);
                            setupModeCheckbox.checked = false;
                            chrome.storage.local.set({ setupMode: false });
                        } else {
                            console.log('Toggle setup response:', response);
                            sendDebugLog(`Toggle setup response: ${JSON.stringify(response)}`);
                        }
                    });
                } else {
                    statusDiv.textContent = 'Error: Open a Whatnot stream page first';
                    statusDiv.className = 'error';
                    setupModeCheckbox.checked = false;
                    chrome.storage.local.set({ setupMode: false });
                    sendDebugLog('Setup mode disabled: Not on a Whatnot page');
                }
            });
        });
    });

    // Test button
    testButton.addEventListener('click', () => {
        chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
            if (tabs[0] && tabs[0].url.match(/^https:\/\/.*\.whatnot\.com\/.*/)) {
                console.log('Sending test_settings to tab:', tabs[0].id);
                sendDebugLog(`Sending test_settings to tab ${tabs[0].id}`);
                chrome.tabs.sendMessage(tabs[0].id, { type: 'test_settings' }, (response) => {
                    if (chrome.runtime.lastError) {
                        console.error('Test error:', chrome.runtime.lastError);
                        statusDiv.textContent = 'Error: Reload the Whatnot page';
                        statusDiv.className = 'error';
                        sendDebugLog(`Test error: ${chrome.runtime.lastError.message}`);
                        return;
                    }
                    if (response && response.success) {
                        statusDiv.textContent = 'Setup works! Chat is ready';
                        statusDiv.className = 'success';
                        sendDebugLog('Setup test successful');
                    } else {
                        statusDiv.textContent = 'Setup failed. Try setting up again or watch the video';
                        statusDiv.className = 'error';
                        sendDebugLog('Setup test failed');
                    }
                });
            } else {
                statusDiv.textContent = 'Error: Open a Whatnot stream page first';
                statusDiv.className = 'error';
                sendDebugLog('Test settings failed: Not on a Whatnot page');
            }
        });
    });
});
"

write_file "$PROJECT_DIR/whatnot_extension/content.js" "// Version History: 0.7.2 -> 0.7.3
console.log('Content script initialized');

(function () {
    let chatInputSelector = '';
    let chatContainerSelector = '';
    let messageItemSelector = '';
    let usernameSelector = '';
    let messageTextSelector = '';
    let ws = null;
    let debugWs = null;
    let controlPanel = null;
    let currentSelectorType = null;
    let selectorIndex = 0;
    let handleMouseMove = null;
    let handleClick = null;

    const selectorTypes = [
        { id: 'chatContainer', prompt: 'where all chat messages show up' },
        { id: 'message', prompt: 'one single chat message' },
        { id: 'user', prompt: 'a username in a chat message' },
        { id: 'text', prompt: 'the text of a chat message' }
    ];
    const selectors = {
        chatContainer: '',
        message: '',
        user: '',
        text: ''
    };

    // Initialize debug WebSocket
    function initDebugWebSocket() {
        debugWs = new WebSocket('ws://localhost:8000/ws/debug');
        debugWs.onopen = () => {
            console.log('Debug WebSocket connected');
            sendDebugLog('Content script WebSocket connected');
        };
        debugWs.onclose = () => {
            console.log('Debug WebSocket disconnected, retrying in 5s');
            setTimeout(initDebugWebSocket, 5000);
        };
        debugWs.onerror = (error) => {
            console.error('Debug WebSocket error:', error);
        };
    }
    initDebugWebSocket();

    function sendDebugLog(message) {
        if (debugWs && debugWs.readyState === WebSocket.OPEN) {
            debugWs.send(JSON.stringify({ type: 'debug', message }));
        }
    }

    // Load saved selectors
    chrome.storage.local.get(['chatInputSelector', 'chatContainerSelector', 'messageSelector', 'userSelector', 'textSelector'], (result) => {
        chatInputSelector = result.chatInputSelector || '';
        chatContainerSelector = result.chatContainerSelector || '';
        messageItemSelector = result.messageSelector || '';
        usernameSelector = result.userSelector || '';
        messageTextSelector = result.textSelector || '';
        console.log('Loaded selectors:', result);
        sendDebugLog(`Loaded selectors: ${JSON.stringify(result)}`);
        initializeWebSocket();
        setupChatInput();
        if (chatContainerSelector) {
            setupMutationObserver();
        }
    });

    // Initialize WebSocket
    function initializeWebSocket() {
        if (ws) ws.close();
        ws = new WebSocket('ws://localhost:8000/ws/whatnot');
        ws.onopen = () => {
            console.log('Whatnot WebSocket connected');
            sendDebugLog('Whatnot WebSocket connected');
            queryStatus();
        };
        ws.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                console.log('WebSocket message received:', data);
                sendDebugLog(`WebSocket message received: ${JSON.stringify(data)}`);
                if (data.type === 'pong') {
                    console.log('Received pong from FoSBot');
                    sendDebugLog('Received pong from FoSBot');
                } else if (data.type === 'sendMessage') {
                    handlePostToWhatnot(data.data);
                }
            } catch (e) {
                console.error('Error parsing WebSocket message:', e);
                sendDebugLog(`Error parsing WebSocket message: ${e.message}`);
            }
        };
        ws.onclose = () => {
            console.log('Whatnot WebSocket disconnected');
            sendDebugLog('Whatnot WebSocket disconnected');
            setTimeout(initializeWebSocket, 2000);
        };
        ws.onerror = (error) => {
            console.error('WebSocket error:', error);
            sendDebugLog(`WebSocket error: ${error}`);
        };
    }

    // Setup chat input
    function setupChatInput() {
        if (!chatInputSelector) {
            sendDebugLog('No chat input selector configured');
            return;
        }
        const chatInput = document.querySelector(chatInputSelector);
        if (chatInput) {
            chatInput.addEventListener('focus', () => {
                console.log('Chat input area selected');
                sendDebugLog('Chat input area selected');
                sendMessageToFoSBot({ type: 'inputSelected', data: 'Chat input focused' });
            });
        } else {
            console.warn('Chat input selector not found:', chatInputSelector);
            sendDebugLog(`Chat input selector not found: ${chatInputSelector}`);
        }
    }

    // Setup MutationObserver
    function setupMutationObserver() {
        if (!chatContainerSelector) {
            sendDebugLog('No chat container selector for MutationObserver');
            return;
        }
        const chatContainer = document.querySelector(chatContainerSelector);
        if (chatContainer) {
            const observer = new MutationObserver(captureChatMessages);
            observer.observe(chatContainer, { childList: true, subtree: true });
            console.log('MutationObserver set up for:', chatContainerSelector);
            sendDebugLog(`MutationObserver set up for: ${chatContainerSelector}`);
        } else {
            console.warn('Chat container not found for MutationObserver:', chatContainerSelector);
            sendDebugLog(`Chat container not found for MutationObserver: ${chatContainerSelector}`);
        }
    }

    // Capture chat messages
    function captureChatMessages() {
        if (!chatContainerSelector || !messageItemSelector || !usernameSelector || !messageTextSelector) {
            console.warn('Missing selectors:', {
                chatContainer: chatContainerSelector,
                message: messageItemSelector,
                user: usernameSelector,
                text: messageTextSelector
            });
            sendDebugLog(`Missing selectors: chatContainer=${chatContainerSelector}, message=${messageItemSelector}, user=${usernameSelector}, text=${messageTextSelector}`);
            return false;
        }
        const chatContainer = document.querySelector(chatContainerSelector);
        if (!chatContainer) {
            console.warn('Chat container not found:', chatContainerSelector);
            sendDebugLog(`Chat container not found: ${chatContainerSelector}`);
            return false;
        }
        const messages = Array.from(chatContainer.querySelectorAll(messageItemSelector)).map(item => ({
            username: item.querySelector(usernameSelector)?.textContent.trim() || 'Unknown',
            message: item.querySelector(messageTextSelector)?.textContent.trim() || ''
        }));
        if (messages.length > 0) {
            console.log('Captured Whatnot messages:', messages);
            sendDebugLog(`Captured Whatnot messages: ${JSON.stringify(messages)}`);
            sendMessageToFoSBot({ type: 'chat_message', payload: messages, platform: 'whatnot' });
            return true;
        }
        return false;
    }

    // Handle message submission
    function handlePostToWhatnot(message) {
        if (!chatInputSelector) {
            console.warn('No chat input selector');
            sendDebugLog('No chat input selector for posting message');
            return;
        }
        const chatInput = document.querySelector(chatInputSelector);
        const submitButton = document.querySelector('button[type=\"submit\"], [data-testid=\"send-message\"]');
        if (chatInput && submitButton) {
            chatInput.value = message;
            submitButton.click();
            console.log('Message submitted to Whatnot:', message);
            sendDebugLog(`Message submitted to Whatnot: ${message}`);
            sendMessageToFoSBot({ type: 'messageSubmitted', data: message, platform: 'whatnot' });
        } else {
            console.warn('Chat input or submit button not found:', { chatInput, submitButton });
            sendDebugLog(`Chat input or submit button not found: input=${chatInput}, button=${submitButton}`);
        }
    }

    // Send message to FoSBot
    function sendMessageToFoSBot(message) {
        if (ws && ws.readyState === WebSocket.OPEN) {
            ws.send(JSON.stringify(message));
            console.log('Sent message to FoSBot:', message);
            sendDebugLog(`Sent message to FoSBot: ${JSON.stringify(message)}`);
        } else {
            console.warn('WebSocket not connected:', message);
            sendDebugLog(`WebSocket not connected for message: ${JSON.stringify(message)}`);
        }
    }

    // Query status
    function queryStatus() {
        sendMessageToFoSBot({ type: 'queryStatus' });
    }

    // Create control panel
    function createControlPanel() {
        if (controlPanel) controlPanel.remove();
        if (selectorIndex >= selectorTypes.length || selectorIndex < 0) {
            console.error('Invalid selector index:', selectorIndex);
            sendDebugLog(`Invalid selector index: ${selectorIndex}`);
            selectorIndex = 0;
        }
        controlPanel = document.createElement('div');
        controlPanel.style.cssText = `
            position: fixed; top: 10px; right: 10px; width: 300px; background: white;
            border: 1px solid #ccc; padding: 15px; z-index: 100000; box-shadow: 0 0 10px rgba(0,0,0,0.3);
            font-family: Arial, sans-serif; font-size: 14px;
        `;
        controlPanel.innerHTML = `
            <h3 style="margin: 0 0 10px;">Set Up Whatnot Chat</h3>
            <p id="instruction">Click ${selectorTypes[selectorIndex].prompt}</p>
            <div id="status" style="color: green; margin-bottom: 10px;"></div>
            <div id="error" style="color: red; margin-bottom: 10px;"></div>
            <button id="nextButton" style="padding: 8px; background: #007bff; color: white; border: none; cursor: pointer;">Next</button>
            <button id="doneButton" style="padding: 8px; margin-left: 10px; background: #28a745; color: white; border: none; cursor: pointer;">Done</button>
            <button id="cancelButton" style="padding: 8px; margin-left: 10px; background: #dc3545; color: white; border: none; cursor: pointer;">Cancel</button>
        `;
        document.body.appendChild(controlPanel);
        console.log('Control panel created for:', selectorTypes[selectorIndex].id);
        sendDebugLog(`Control panel created for: ${selectorTypes[selectorIndex].id}`);

        document.getElementById('nextButton').addEventListener('click', () => {
            if (selectors[selectorTypes[selectorIndex].id]) {
                selectorIndex++;
                if (selectorIndex < selectorTypes.length) {
                    currentSelectorType = selectorTypes[selectorIndex].id;
                    document.getElementById('instruction').textContent = `Click ${selectorTypes[selectorIndex].prompt}`;
                    document.getElementById('status').textContent = '';
                    sendDebugLog(`Advanced to next selector: ${selectorTypes[selectorIndex].id}`);
                } else {
                    document.getElementById('instruction').textContent = 'All set! Click Done to finish';
                    document.getElementById('nextButton').disabled = true;
                    sendDebugLog('All selectors set, prompting to finish');
                }
            } else {
                document.getElementById('error').textContent = 'Please click an element first';
                sendDebugLog('Next button clicked but no element selected');
            }
        });

        document.getElementById('doneButton').addEventListener('click', () => {
            saveSelectors();
            cleanup();
            sendDebugLog('Done button clicked, selectors saved');
        });

        document.getElementById('cancelButton').addEventListener('click', () => {
            cleanup();
            sendDebugLog('Cancel button clicked, setup aborted');
        });
    }

    function saveSelectors() {
        const settings = {
            chatContainerSelector: selectors.chatContainer,
            messageSelector: selectors.message,
            userSelector: selectors.user,
            textSelector: selectors.text,
            setupMode: false
        };
        chrome.storage.local.set(settings, () => {
            console.log('Selectors saved:', settings);
            sendDebugLog(`Selectors saved: ${JSON.stringify(settings)}`);
            chatContainerSelector = settings.chatContainerSelector;
            messageItemSelector = settings.messageSelector;
            usernameSelector = settings.userSelector;
            messageTextSelector = settings.textSelector;
            setupMutationObserver();
            chrome.runtime.sendMessage({ type: 'update_settings', payload: settings });
        });
    }

    function cleanup() {
        if (controlPanel) controlPanel.remove();
        document.querySelectorAll('.fosbot-overlay, .fosbot-highlight').forEach(el => el.remove());
        if (handleMouseMove) document.removeEventListener('mousemove', handleMouseMove);
        if (handleClick) document.removeEventListener('click', handleClick);
        controlPanel = null;
        currentSelectorType = null;
        selectorIndex = 0;
        handleMouseMove = null;
        handleClick = null;
        chrome.storage.local.set({ setupMode: false });
        console.log('Selector cleanup completed');
        sendDebugLog('Selector cleanup completed');
    }

    function startSetup() {
        console.log('Starting setup');
        sendDebugLog('Starting setup process');
        document.querySelectorAll('.fosbot-overlay, .fosbot-highlight').forEach(el => el.remove());

        const overlay = document.createElement('div');
        overlay.className = 'fosbot-overlay';
        overlay.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.5); z-index:99998;';
        document.body.appendChild(overlay);
        console.log('Overlay added');
        sendDebugLog('Overlay added');

        const highlight = document.createElement('div');
        highlight.className = 'fosbot-highlight';
        highlight.style.cssText = 'position:absolute; border:2px dashed #fff; z-index:99999; pointer-events:none;';
        document.body.appendChild(highlight);
        console.log('Highlight added');
        sendDebugLog('Highlight added');

        const getElementAtPoint = (x, y) => {
            overlay.style.pointerEvents = 'none';
            const el = document.elementFromPoint(x, y);
            overlay.style.pointerEvents = 'auto';
            return el;
        };

        handleMouseMove = (e) => {
            const el = getElementAtPoint(e.clientX, e.clientY);
            if (el) {
                console.log('Mouse over element:', el.tagName, el.className);
                sendDebugLog(`Mouse over element: ${el.tagName}, class=${el.className}`);
                const rect = el.getBoundingClientRect();
                highlight.style.left = `${rect.left}px`;
                highlight.style.top = `${rect.top}px`;
                highlight.style.width = `${rect.width}px`;
                highlight.style.height = `${rect.height}px`;
            }
        };

        handleClick = (e) => {
            e.preventDefault();
            e.stopPropagation();
            const el = getElementAtPoint(e.clientX, e.clientY);
            if (el) {
                const selector = generateRobustSelector(el);
                console.log('Element clicked, selector:', selector);
                sendDebugLog(`Element clicked, selector: ${selector}`);
                selectors[currentSelectorType] = selector;
                document.getElementById('status').textContent = `Set: ${selectorTypes[selectorIndex].prompt}`;
                document.getElementById('error').textContent = '';
            }
        };

        document.addEventListener('mousemove', handleMouseMove);
        document.addEventListener('click', handleClick);
    }

    // Selector generation
    function generateRobustSelector(el) {
        if (el.id) return `#${el.id}`;
        let path = [];
        let current = el;
        while (current && current.nodeType === Node.ELEMENT_NODE && current !== document.body) {
            let selector = current.nodeName.toLowerCase();
            if (current.className && typeof current.className === 'string') {
                const classes = current.className.trim().split(/\s+/).join('.');
                if (classes) selector += `.${classes}`;
            }
            path.unshift(selector);
            current = current.parentNode;
        }
        return path.join(' > ');
    }

    // Handle messages
    chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
        console.log('Content script received message:', message);
        sendDebugLog(`Content script received message: ${JSON.stringify(message)}`);
        if (message.type === 'toggle_setup_mode') {
            console.log('Toggle setup mode:', message.payload.setupMode);
            sendDebugLog(`Toggle setup mode: ${message.payload.setupMode}`);
            if (message.payload.setupMode) {
                selectorIndex = 0;
                currentSelectorType = selectorTypes[0].id;
                createControlPanel();
                startSetup();
            } else {
                cleanup();
            }
            sendResponse({ success: true });
        } else if (message.type === 'query_status') {
            sendResponse({
                wsConnected: ws && ws.readyState === WebSocket.OPEN,
                selectorsValid: !!chatContainerSelector && !!messageItemSelector && !!usernameSelector && !!messageTextSelector
            });
            sendDebugLog(`Query status response: wsConnected=${ws && ws.readyState === WebSocket.OPEN}, selectorsValid=${!!chatContainerSelector && !!messageItemSelector && !!usernameSelector && !!messageTextSelector}`);
        } else if (message.type === 'update_settings') {
            console.log('Updating selectors:', message.payload);
            sendDebugLog(`Updating selectors: ${JSON.stringify(message.payload)}`);
            chatInputSelector = message.payload.chatInputSelector || '';
            chatContainerSelector = message.payload.chatContainerSelector || '';
            messageItemSelector = message.payload.messageSelector || '';
            usernameSelector = message.payload.userSelector || '';
            messageTextSelector = message.payload.textSelector || '';
            setupChatInput();
            if (chatContainerSelector) {
                setupMutationObserver();
            }
            captureChatMessages();
            sendResponse({ success: true });
        } else if (message.type === 'test_settings') {
            const success = captureChatMessages();
            sendResponse({ success });
            sendDebugLog(`Test settings result: ${success}`);
        }
        return true; // Keep channel open for async response
    });

    // Initialize on page load
    window.addEventListener('load', () => {
        console.log('Whatnot Chat Consolidator loaded');
        sendDebugLog('Whatnot Chat Consolidator loaded');
        setInterval(captureChatMessages, 2000);
    });
})();
"

# data/ Directory Files
write_file "$PROJECT_DIR/data/oauth_states.json" "# Version History: 0.7.2 -> 0.7.3
{}"

write_file "$PROJECT_DIR/data/settings.json" "# Version History: 0.7.2 -> 0.7.3
{}"

write_file "$PROJECT_DIR/data/commands.json" "# Version History: 0.7.2 -> 0.7.3
{
    \"test\": \"this is just a test\",
    \"ween\": \"Ask Mystic\"
}"

write_file "$PROJECT_DIR/data/tokens.json" "# Version History: 0.7.2 -> 0.7.3
{}"

# Create Whatnot extension ZIP
echo "Creating Whatnot extension ZIP..."
cd "$PROJECT_DIR/whatnot_extension"
zip -r "$PROJECT_DIR/static/whatnot_extension.zip" ./*
cd "$PROJECT_DIR"
echo "Created $PROJECT_DIR/static/whatnot_extension.zip"

# Verify files
echo "Verifying files..."
for file in "${files[@]}"; do
    if [ -f "$PROJECT_DIR/$file" ]; then
        echo "Verified: $file"
    else
        echo "Error: $file not created"
    fi
done

echo "File replacement complete. Backup saved to $BACKUP_DIR"
echo "Next steps:"
echo "1. Ensure .env has valid API keys and tokens."
echo "2. Run: source venv/bin/activate"
echo "3. Run: pip install -r requirements.txt"
echo "4. Run: uvicorn app.main:app --host localhost --port 8000"
echo "5. Load the Whatnot extension in Chrome (chrome://extensions/)."