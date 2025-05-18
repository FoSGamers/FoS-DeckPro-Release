# --- File: app/core/config.py --- START ---
import os
from dotenv import load_dotenv
from pathlib import Path
import logging
import warnings

# Determine project root based on this file's location
project_root = Path(__file__).parent.parent.parent
env_path = project_root / '.env'

# Load .env file from project root
loaded_env = load_dotenv(dotenv_path=env_path, verbose=True)
if loaded_env:
    print(f"Loaded .env config from: {env_path}") # Use print as logger not setup yet
else:
    print(f"INFO: .env file not found at {env_path}. Using defaults/env vars.") # Use print

# --- Load General App Settings ---
COMMAND_PREFIX = os.getenv("COMMAND_PREFIX", "!")
WS_HOST = os.getenv("WS_HOST", "localhost")
WS_PORT = int(os.getenv("WS_PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
DATA_DIR = Path(os.getenv("DATA_DIR", project_root / "data")) # Get data dir path

# --- Load OAuth Application Credentials ---
# These are for YOUR application, not the end-user
TWITCH_APP_CLIENT_ID = os.getenv("TWITCH_APP_CLIENT_ID")
TWITCH_APP_CLIENT_SECRET = os.getenv("TWITCH_APP_CLIENT_SECRET")
# Add placeholders for others later
# YOUTUBE_APP_CLIENT_ID = os.getenv("YOUTUBE_APP_CLIENT_ID")
# YOUTUBE_APP_CLIENT_SECRET = os.getenv("YOUTUBE_APP_CLIENT_SECRET")
# X_APP_CLIENT_ID = os.getenv("X_APP_CLIENT_ID")
# X_APP_CLIENT_SECRET = os.getenv("X_APP_CLIENT_SECRET")

# --- Load Security Keys ---
APP_SECRET_KEY = os.getenv("APP_SECRET_KEY")

# --- Basic Logging Setup ---
log_level_int = getattr(logging, LOG_LEVEL, logging.INFO)
logging.basicConfig(
    level=log_level_int,
    format='%(asctime)s - %(name)s [%(levelname)s] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
# Quiet down noisy libraries unless debugging them specifically
logging.getLogger("twitchio").setLevel(logging.WARNING)
logging.getLogger("websockets").setLevel(logging.WARNING)
logging.getLogger("google").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("watchfiles").setLevel(logging.WARNING) # Uvicorn reloader log

# Logger for this config module itself
logger = logging.getLogger(__name__)
logger.setLevel(log_level_int)

logger.info(f"Config Loaded: Prefix='{COMMAND_PREFIX}', WS={WS_HOST}:{WS_PORT}, LogLevel={LOG_LEVEL}, DataDir='{DATA_DIR}'")

# --- Configuration Validation ---
# Validate essential non-secret config
if not APP_SECRET_KEY:
    warnings.warn("CRITICAL SECURITY WARNING: APP_SECRET_KEY is not set in .env or environment variables. OAuth state validation will be insecure. Please generate a strong key.", RuntimeWarning)
    # In a real app, you might want to exit here if the secret key is missing.
    # For local dev with this single-user app, a warning might suffice initially,
    # but it's crucial for preventing CSRF.
    APP_SECRET_KEY = "insecure_default_key_replace_me" # Fallback for dev ONLY

# Validate Twitch App Credentials (only if planning to use Twitch OAuth)
if not TWITCH_APP_CLIENT_ID:
     logger.warning("Twitch OAuth configuration missing: TWITCH_APP_CLIENT_ID not set.")
if not TWITCH_APP_CLIENT_SECRET:
     logger.warning("Twitch OAuth configuration missing: TWITCH_APP_CLIENT_SECRET not set.")


# Ensure data directory exists
try:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory verified/created: {DATA_DIR.resolve()}")
except OSError as e:
    logger.error(f"CRITICAL: Could not create/access data directory '{DATA_DIR}': {e}")
    # Application might still run but storage will fail.

# NOTE: User API Tokens are NOT loaded here. They are loaded on demand
# by services from the JSON store after the OAuth flow.
# --- File: app/core/config.py --- END ---