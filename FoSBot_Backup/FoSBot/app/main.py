# Version History: 0.7.2 -> 0.7.3
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
    "twitch": {"start": start_twitch_service_task, "stop": stop_twitch_service},
    "youtube": {"start": start_youtube_service_task, "stop": stop_youtube_service},
    "x": {"start": start_x_service_task, "stop": stop_x_service},
    "whatnot": {"start": start_whatnot_bridge_task, "stop": stop_whatnot_bridge},
}

async def handle_service_control(event: ServiceControl):
    """Handles start/stop/restart commands for services via the event bus."""
    logger.info(f"Handling control: '{event.command}' for '{event.service_name}'...")
    logger.debug(f"Service control event details: {event}")
    control_funcs = service_control_map.get(event.service_name)
    current_task = _service_tasks_map.get(event.service_name)

    if not control_funcs:
        logger.error(f"No control functions found for service '{event.service_name}'.")
        return

    start_func = control_funcs.get("start")
    stop_func = control_funcs.get("stop")

    if event.command == "stop":
        if current_task and not current_task.done():
            logger.info(f"Stopping running/starting service '{event.service_name}'...")
            if stop_func:
                try:
                    await stop_func()
                    logger.info(f"Service '{event.service_name}' stopped successfully.")
                except Exception as e:
                    logger.error(f"Error stopping service '{event.service_name}': {e}")
            else:
                logger.warning(f"No stop function defined but task exists for '{event.service_name}'. Cancelling directly.")
                if not current_task.cancelled():
                    current_task.cancel()
        else:
            logger.info(f"Service '{event.service_name}' not running, no stop action needed.")
        _service_tasks_map[event.service_name] = None

    elif event.command == "start":
        if current_task and not current_task.done():
            logger.warning(f"Service '{event.service_name}' already running or starting.")
            return

        if start_func:
            logger.info(f"Executing start for '{event.service_name}'...")
            try:
                new_task = start_func()
                if new_task and isinstance(new_task, asyncio.Task):
                    _service_tasks_map[event.service_name] = new_task
                    background_tasks.add(new_task)
                    new_task.add_done_callback(background_tasks.discard)
                    logger.info(f"Task for '{event.service_name}' started and added to background tasks.")
                elif new_task is None:
                    logger.warning(f"Start function for '{event.service_name}' did not return a task (disabled/failed pre-check?).")
                else:
                    logger.error(f"Start function for '{event.service_name}' returned invalid object: {type(new_task)}")
            except Exception as e:
                logger.error(f"Error starting service '{event.service_name}': {e}")
        else:
            logger.warning(f"No start function defined for '{event.service_name}'.")

    elif event.command == "restart":
        logger.info(f"Executing restart for '{event.service_name}'...")
        if current_task and not current_task.done():
            logger.info("...stopping existing service first.")
            if stop_func:
                try:
                    await stop_func()
                    await asyncio.sleep(1)
                    logger.info(f"Service '{event.service_name}' stopped for restart.")
                except Exception as e:
                    logger.error(f"Error stopping service '{event.service_name}' for restart: {e}")
            else:
                logger.warning(f"No stop function for restart of '{event.service_name}'. Cancelling directly.")
                if not current_task.cancelled():
                    current_task.cancel()
                await asyncio.sleep(0.1)
        else:
            logger.info("...service not running, attempting start.")

        _service_tasks_map[event.service_name] = None

        if start_func:
            logger.info("...starting new service instance.")
            try:
                new_task = start_func()
                if new_task and isinstance(new_task, asyncio.Task):
                    _service_tasks_map[event.service_name] = new_task
                    background_tasks.add(new_task)
                    new_task.add_done_callback(background_tasks.discard)
                    logger.info(f"Task for '{event.service_name}' added after restart.")
                elif new_task is None:
                    logger.warning(f"Start function for '{event.service_name}' did not return task on restart.")
                else:
                    logger.error(f"Start function '{event.service_name}' returned invalid object on restart: {type(new_task)}")
            except Exception as e:
                logger.error(f"Error restarting service '{event.service_name}': {e}")
        else:
            logger.warning(f"No start function available for restart of '{event.service_name}'.")

# Lifespan Manager
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("--- Application startup sequence initiated ---")
    logger.info("Starting event bus worker..."); await event_bus.start()
    logger.info("Setting up event listeners...")
    try:
        await setup_chat_processor()
        logger.debug("Chat processor setup completed")
    except Exception as e:
        logger.error(f"Error setting up chat processor: {e}")
    setup_dashboard_service_listeners()
    setup_streamer_command_handler()
    event_bus.subscribe(ServiceControl, handle_service_control)
    logger.info("Service control handler subscribed.")
    logger.info("Services will start only via user action through the dashboard.")
    logger.info("--- Application startup complete. Running! ---")

    yield

    logger.info("--- Application shutdown sequence initiated ---")
    logger.info("Stopping platform services (sending stop commands)...")
    stop_tasks = [
        handle_service_control(ServiceControl(service_name=name, command="stop"))
        for name in service_control_map.keys()
    ]
    try:
        await asyncio.gather(*stop_tasks, return_exceptions=True)
    except Exception as e:
        logger.error(f"Error stopping services: {e}")

    logger.info("Waiting briefly..."); await asyncio.sleep(1)
    logger.info("Stopping event bus worker..."); await event_bus.stop()

    if background_tasks:
        logger.warning(f"Cancelling {len(background_tasks)} lingering background tasks...")
        for task in list(background_tasks):
            if task and not task.done():
                task.cancel()
        try:
            await asyncio.wait_for(asyncio.gather(*background_tasks, return_exceptions=True), timeout=5.0)
            logger.debug("Cancelled background tasks successfully.")
        except asyncio.TimeoutError:
            logger.error("Timeout waiting for background tasks to cancel.")
        except Exception as e:
            logger.exception(f"Error during task cancellation: {e}")
    else:
        logger.info("No lingering background tasks found.")
    logger.info("--- Application shutdown complete. ---")

# FastAPI App Creation
app = FastAPI(
    title="FoSBot (Whatnot + YouTube + Twitch + X)",
    version="0.7.3",
    lifespan=lifespan
)

# Serve whatnot_extension.zip from project root
@app.get("/whatnot_extension.zip")
async def serve_whatnot_extension():
    zip_path = Path("whatnot_extension.zip")
    if not zip_path.is_file():
        zip_path = Path("static/whatnot_extension.zip")
        if not zip_path.is_file():
            raise HTTPException(status_code=404, detail="Whatnot extension ZIP file not found")
    return FileResponse(zip_path, media_type="application/zip", filename="whatnot_extension.zip")

# Mount Routers
app.include_router(auth_api.router)
app.include_router(ws_endpoints.router, prefix="/ws")
app.include_router(settings_api.router, prefix="/api", tags=["Settings & Control"])
app.include_router(commands_api.router, prefix="/api", tags=["Commands"])

# Mount Static Files
STATIC_DIR = "static"
static_path = Path(STATIC_DIR)
if not static_path.is_dir():
    logger.error(f"Static files directory '{STATIC_DIR}' not found at {static_path.resolve()}. Dashboard UI unavailable.")
else:
    try:
        app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="static")
        logger.info(f"Mounted static files for dashboard UI from './{STATIC_DIR}'.")
    except Exception as e:
        logger.exception(f"Failed to mount static files directory './{STATIC_DIR}': {e}")

# Direct Run (Debugging Only)
if __name__ == "__main__":
    import uvicorn
    logger.warning("Running via main.py is intended for debugging ONLY. Use 'uvicorn app.main:app --reload'.")
    uvicorn.run("app.main:app", host=settings['WS_HOST'], port=settings['WS_PORT'], log_level=settings['LOG_LEVEL'].lower(), reload=True)

