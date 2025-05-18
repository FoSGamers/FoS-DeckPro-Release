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

