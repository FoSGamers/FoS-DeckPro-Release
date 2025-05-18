# Version History: 0.7.2 -> 0.7.3
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

@router.get("/settings")
async def get_settings():
    logger.debug("Returning settings")
    return settings

@router.post("/settings")
async def update_settings(new_settings: AllSettingsModel):
    logger.info("Received settings update request")
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
        logger.info("Settings updated and event published")
    return {"status": "success"}

@router.post("/control/{service}/{command}")
async def control_service(service: str, command: str):
    logger.info(f"Received control request: {command} for {service}")
    if service not in ['twitch', 'youtube', 'x', 'whatnot']:
        raise HTTPException(status_code=400, detail="Invalid service")
    if command not in ["start", "stop", "restart"]:
        raise HTTPException(status_code=400, detail="Invalid command")
    event_bus.publish(ServiceControl(service_name=service, command=command))
    return {"status": "success"}

