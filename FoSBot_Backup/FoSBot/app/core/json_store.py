# Version History: 0.7.2 -> 0.7.3
import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict
import aiofiles

logger = logging.getLogger(__name__)

async def load_json_data(file_path: Path) -> Dict[str, Any]:
    """Load JSON data from a file with async file locking."""
    try:
        async with aiofiles.open(file_path, mode='r') as f:
            content = await f.read()
        return json.loads(content) if content else {}
    except FileNotFoundError:
        logger.warning(f"JSON file not found, creating new: {file_path}")
        return {}
    except json.JSONDecodeError:
        logger.error(f"Invalid JSON in {file_path}, returning empty dict")
        return {}
    except Exception as e:
        logger.error(f"Error loading JSON from {file_path}: {e}")
        return {}

async def save_json_data(file_path: Path, data: Dict[str, Any]) -> None:
    """Save JSON data to a file with async file locking."""
    try:
        os.makedirs(file_path.parent, exist_ok=True)
        async with aiofiles.open(file_path, mode='w') as f:
            await f.write(json.dumps(data, indent=2))
        logger.debug(f"Saved JSON to {file_path}")
    except Exception as e:
        logger.error(f"Error saving JSON to {file_path}: {e}")

