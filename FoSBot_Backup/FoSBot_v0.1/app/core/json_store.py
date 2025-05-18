# --- File: app/core/json_store.py --- START ---
import json
import logging
import aiofiles
import asyncio
from pathlib import Path
from typing import Dict, Any, Optional, Union
from collections import defaultdict
import time # Import time for expiry calculations

# Ensure config is imported correctly if needed (for DATA_DIR)
from app.core.config import DATA_DIR

logger = logging.getLogger(__name__)

# Use defaultdict for the locks for simplicity
_file_locks: Dict[Path, asyncio.Lock] = defaultdict(asyncio.Lock)

async def load_json_data(filename: str, default: Any = None) -> Optional[Any]:
    """
    Loads data asynchronously from a JSON file in the data directory.
    Handles file not found, empty files, and JSON decode errors gracefully.
    Uses asyncio.Lock per file to prevent read/write race conditions.
    """
    filepath = DATA_DIR / f"{filename}.json"
    lock = _file_locks[filepath] # Get or create lock for this file path
    # logger.debug(f"Acquiring lock for READ: {filepath}") # Too noisy for default DEBUG
    async with lock:
        # logger.debug(f"Lock acquired for READ: {filepath}")
        try:
            if not filepath.is_file():
                logger.warning(f"JSON file not found: {filepath}. Returning default.")
                return default
            # Use aiofiles for async file operations
            async with aiofiles.open(filepath, mode='r', encoding='utf-8') as f:
                content = await f.read()
            # Handle empty file case
            if not content:
                 logger.warning(f"JSON file is empty: {filepath}. Returning default.")
                 return default
            # Decode JSON
            data = json.loads(content)
            # logger.info(f"Successfully loaded data from {filepath}") # Log only on success if needed
            return data
        except json.JSONDecodeError:
            logger.error(f"Error decoding JSON from file: {filepath}. Returning default.", exc_info=True)
            return default
        except Exception as e:
            logger.error(f"Unexpected error loading JSON file {filepath}: {e}", exc_info=True)
            return default
        finally:
            pass # logger.debug(f"Released lock for READ: {filepath}")

async def save_json_data(filename: str, data: Any) -> bool:
    """
    Saves data asynchronously to a JSON file in the data directory.
    Uses a temporary file and atomic rename for safer writes.
    Uses asyncio.Lock per file to prevent write races.
    """
    filepath = DATA_DIR / f"{filename}.json"
    lock = _file_locks[filepath] # Get or create lock
    task_id_part = id(asyncio.current_task()) if asyncio.current_task() else 'notask'
    temp_filepath = filepath.with_suffix(f'.{task_id_part}.tmp')

    # logger.debug(f"Acquiring lock for WRITE: {filepath}")
    async with lock:
        # logger.debug(f"Lock acquired for WRITE: {filepath}")
        try:
            async with aiofiles.open(temp_filepath, mode='w', encoding='utf-8') as f:
                await f.write(json.dumps(data, indent=4, ensure_ascii=False))
            temp_filepath.rename(filepath)
            logger.info(f"Successfully saved data to {filepath}")
            return True
        except Exception as e:
            logger.error(f"Error saving JSON file {filepath}: {e}", exc_info=True)
            if temp_filepath.exists():
                try: temp_filepath.unlink(); logger.debug(f"Removed temporary file {temp_filepath} after error.")
                except OSError as unlink_e: logger.error(f"Error removing temporary file {temp_filepath}: {unlink_e}")
            return False
        finally:
             pass # logger.debug(f"Released lock for WRITE: {filepath}")

# --- Specific Settings and Data File Management ---
SETTINGS_FILE = "settings"
CHECKINS_FILE = "checkins"
COUNTERS_FILE = "counters"

# --- Token Management ---
# Structure within settings.json:
# {
#   "twitch_access_token": "...",
#   "twitch_refresh_token": "...",
#   "twitch_expires_at": 1678886400.123, # Timestamp (time.time() + expires_in)
#   "twitch_scopes": ["chat:read", "chat:edit"],
#   "twitch_user_id": "12345",
#   "twitch_user_login": "fos_gamers",
#   "youtube_access_token": "...",
#   ... other settings like COMMAND_PREFIX ...
# }

async def save_tokens(platform: str, token_data: Dict[str, Any]) -> bool:
    """
    Saves OAuth token data for a specific platform into settings.json.
    Expects token_data to contain 'access_token', 'refresh_token', 'expires_in', 'scope'.
    Also saves 'user_id' and 'user_login' if provided.
    """
    logger.info(f"Attempting to save tokens for platform: {platform}")
    settings = await load_settings() # Load current settings
    if settings is None: settings = {}

    if 'access_token' not in token_data:
        logger.error(f"Missing 'access_token' in token_data for {platform}. Cannot save.")
        return False

    settings[f"{platform}_access_token"] = token_data['access_token']
    # Refresh token might not always be provided (e.g., during refresh itself)
    if 'refresh_token' in token_data:
        settings[f"{platform}_refresh_token"] = token_data['refresh_token']
    if 'expires_in' in token_data:
        # Calculate expiry timestamp (seconds since epoch)
        expires_at = time.time() + int(token_data['expires_in']) - 300 # Subtract 5 mins buffer
        settings[f"{platform}_expires_at"] = expires_at
    if 'scope' in token_data:
        # Scope might be a list or space-separated string depending on platform/library
        scopes = token_data['scope']
        if isinstance(scopes, str):
            scopes = scopes.split() # Split space-separated string into list
        settings[f"{platform}_scopes"] = scopes

    # Store optional user info if available (useful for display/logging)
    if 'user_id' in token_data:
        settings[f"{platform}_user_id"] = str(token_data['user_id'])
    if 'user_login' in token_data:
        settings[f"{platform}_user_login"] = token_data['user_login']

    logger.warning(f"Saving OAuth tokens for {platform} to plain JSON file. Ensure file permissions are secure.")
    return await save_settings(settings) # Save the modified settings dict

async def load_tokens(platform: str) -> Optional[Dict[str, Any]]:
    """Loads OAuth token data for a specific platform from settings.json."""
    settings = await load_settings()
    if not settings: return None

    token_info = {
        "access_token": settings.get(f"{platform}_access_token"),
        "refresh_token": settings.get(f"{platform}_refresh_token"),
        "expires_at": settings.get(f"{platform}_expires_at"),
        "scopes": settings.get(f"{platform}_scopes", []),
        "user_id": settings.get(f"{platform}_user_id"),
        "user_login": settings.get(f"{platform}_user_login"),
    }

    # Only return if access token exists
    if token_info["access_token"]:
        # Convert expires_at to float if it's not None
        if token_info["expires_at"] is not None:
             try: token_info["expires_at"] = float(token_info["expires_at"])
             except (ValueError, TypeError): token_info["expires_at"] = None # Invalidate if conversion fails
        return token_info
    else:
        logger.debug(f"No stored access token found for platform: {platform}")
        return None

async def clear_tokens(platform: str) -> bool:
    """Removes OAuth token data for a specific platform from settings.json."""
    logger.info(f"Clearing tokens for platform: {platform}")
    settings = await load_settings()
    if settings is None: return True # Nothing to clear

    keys_to_remove = [
        f"{platform}_access_token", f"{platform}_refresh_token",
        f"{platform}_expires_at", f"{platform}_scopes",
        f"{platform}_user_id", f"{platform}_user_login"
    ]
    updated = False
    for key in keys_to_remove:
        if key in settings:
            del settings[key]
            updated = True

    if updated:
        return await save_settings(settings)
    else:
        return True # No changes needed

# --- Generic Settings Management (Keep for other settings like COMMAND_PREFIX) ---
async def load_settings() -> Dict[str, Any]:
    """Loads the main application settings."""
    settings = await load_json_data(SETTINGS_FILE, default={})
    return settings if isinstance(settings, dict) else {}

async def save_settings(settings_data: Dict[str, Any]) -> bool:
    """Saves the main application settings."""
    return await save_json_data(SETTINGS_FILE, settings_data)

async def get_setting(key: str, default: Any = None) -> Any:
     """Convenience function to get a single non-token setting."""
     # Avoid using this for tokens, use load_tokens instead
     settings = await load_settings()
     return settings.get(key, default)

async def update_setting(key: str, value: Any) -> bool:
    """Updates a single non-token setting."""
    settings = await load_settings()
    if settings is None: settings = {}
    if settings.get(key) != value:
        settings[key] = value
        return await save_settings(settings)
    return True # No change needed

# --- Other Data Management (Unchanged) ---
async def load_checkins() -> Dict[str, Any]:
    """Loads check-in data."""
    checkins = await load_json_data(CHECKINS_FILE, default={})
    return checkins if isinstance(checkins, dict) else {}

async def save_checkins(data: Dict[str, Any]) -> bool:
    """Saves check-in data."""
    return await save_json_data(CHECKINS_FILE, data)

async def load_counters() -> Dict[str, int]:
    """Loads counter data, ensuring values are integers."""
    counters = await load_json_data(COUNTERS_FILE, default={})
    valid_counters = {}
    if isinstance(counters, dict):
        for k, v in counters.items():
            try: valid_counters[k] = int(v)
            except (ValueError, TypeError): logger.warning(f"Invalid value '{v}' for counter '{k}' in {COUNTERS_FILE}.json. Ignoring.")
    return valid_counters

async def save_counters(data: Dict[str, int]) -> bool:
    """Saves counter data."""
    return await save_json_data(COUNTERS_FILE, data)
# --- File: app/core/json_store.py --- END ---