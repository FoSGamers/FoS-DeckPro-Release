# Version History: 0.7.2 -> 0.7.3
from fastapi import APIRouter
from app.core.config import logger, settings
from app.core.json_store import load_json_data, save_json_data
from pathlib import Path

router = APIRouter()

@router.get("/commands")
async def get_commands():
    logger.debug("Fetching all commands")
    commands_file = Path(settings['DATA_DIR']) / 'commands.json'
    commands = await load_json_data(commands_file)
    logger.debug(f"Retrieved commands: {commands}")
    return commands

@router.post("/commands/{command}")
async def add_command(command: str, response: str):
    logger.info(f"Adding command: !{command} with response: {response}")
    commands_file = Path(settings['DATA_DIR']) / 'commands.json'
    commands = await load_json_data(commands_file)
    commands[command] = response
    await save_json_data(commands_file, commands)
    return {"status": "success"}

