# Version History: 0.7.2 -> 0.7.3
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
    logger.info(f"Loaded .env config from: {env_path}")
else:
    logger.warning(f"No .env file found at {env_path}")

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
            logger.info(f"Loaded settings from {settings_file}")
    except Exception as e:
        logger.error(f"Error loading settings from {settings_file}: {e}")
else:
    logger.warning(f"No settings.json found at {settings_file}")

# Create data directory if it doesn't exist
data_dir = Path(settings['DATA_DIR'])
if not data_dir.is_dir():
    data_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Data directory verified/created: {data_dir}")
else:
    logger.info(f"Data directory exists: {data_dir}")

# Save settings to settings.json
try:
    with settings_file.open('w') as f:
        json.dump(settings, f, indent=2)
    logger.debug(f"Saved settings to {settings_file}")
except Exception as e:
    logger.error(f"Error saving settings to {settings_file}: {e}")

