# --- File: app/main.py --- START ---
import asyncio
import logging
import signal
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from pathlib import Path
import sys

# --- Core Imports ---
from app.core.config import logger # Use configured logger
from app.core.event_bus import event_bus

# --- API Routers ---
from app.apis import ws_endpoints, settings_api
from app.apis import auth_api # <-- Import the new auth router

# --- Service Control & Setup ---
from app.services.twitch_service import start_twitch_service_task, stop_twitch_service
from app.services.youtube_service import start_youtube_service_task, stop_youtube_service
from app.services.x_service import start_x_service_task, stop_x_service
from app.services.whatnot_bridge import start_whatnot_bridge_task, stop_whatnot_bridge
from app.services.chat_processor import setup_chat_processor
from app.services.dashboard_service import setup_dashboard_service_listeners
from app.services.streamer_command_handler import setup_streamer_command_handler

# --- Events ---
from app.events import ServiceControl

# --- Global State ---
background_tasks = set()
_service_tasks_map: dict[str, asyncio.Task | None] = {} # Store running tasks by name

# --- Service Control Mapping ---
service_control_map = {
    "twitch": {"start": start_twitch_service_task, "stop": stop_twitch_service},
    "youtube": {"start": start_youtube_service_task, "stop": stop_youtube_service},
    "x": {"start": start_x_service_task, "stop": stop_x_service},
    "whatnot": {"start": start_whatnot_bridge_task, "stop": stop_whatnot_bridge},
}

async def handle_service_control(event: ServiceControl):
    """Handles start/stop/restart commands for services via the event bus."""
    logger.info(f"Handling control: '{event.command}' for '{event.service_name}'...")
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
            if stop_func: await stop_func()
            else: logger.warning(f"No stop function defined but task exists for '{event.service_name}'.")
        else:
             logger.info(f"Service '{event.service_name}' not running, no stop action needed.")
        _service_tasks_map[event.service_name] = None # Clear task reference after stop

    elif event.command == "start":
        if current_task and not current_task.done():
            logger.warning(f"Service '{event.service_name}' already running or starting.")
            return

        if start_func:
            logger.info(f"Executing start for '{event.service_name}'...")
            new_task = start_func() # Start func handles async task creation
            if new_task and isinstance(new_task, asyncio.Task):
                _service_tasks_map[event.service_name] = new_task
                background_tasks.add(new_task)
                # Remove task from set when it finishes (success, error, or cancel)
                new_task.add_done_callback(background_tasks.discard)
                logger.info(f"Task for '{event.service_name}' started and added to background tasks.")
            elif new_task is None:
                 logger.warning(f"Start function for '{event.service_name}' did not return a task (disabled/failed pre-check?).")
            else:
                 logger.error(f"Start function for '{event.service_name}' returned invalid object: {type(new_task)}")
        else:
            logger.warning(f"No start function defined for '{event.service_name}'.")

    elif event.command == "restart":
        logger.info(f"Executing restart for '{event.service_name}'...")
        if current_task and not current_task.done():
            logger.info("...stopping existing service first.")
            if stop_func:
                 await stop_func()
                 await asyncio.sleep(1) # Brief pause for graceful shutdown
            else: logger.warning(f"No stop function for restart of '{event.service_name}'.")
        else:
             logger.info("...service not running, attempting start.")

        _service_tasks_map[event.service_name] = None # Ensure old task ref is cleared

        if start_func:
            logger.info("...starting new service instance.")
            new_task = start_func()
            if new_task and isinstance(new_task, asyncio.Task):
                _service_tasks_map[event.service_name] = new_task
                background_tasks.add(new_task)
                new_task.add_done_callback(background_tasks.discard)
                logger.info(f"Task for '{event.service_name}' added after restart.")
            elif new_task is None: logger.warning(f"Start function for '{event.service_name}' did not return task on restart.")
            else: logger.error(f"Start function '{event.service_name}' returned invalid object on restart: {type(new_task)}")
        else:
            logger.warning(f"No start function available for restart of '{event.service_name}'.")

# --- Lifespan Manager ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and shutdown events."""
    logger.info("--- Application startup sequence initiated ---")
    logger.info("Starting event bus worker..."); await event_bus.start()
    logger.info("Setting up event listeners...");
    setup_chat_processor()
    setup_dashboard_service_listeners()
    setup_streamer_command_handler()
    event_bus.subscribe(ServiceControl, handle_service_control) # Subscribe control handler
    logger.info("Service control handler subscribed.")
    logger.info("Services will start automatically IF valid OAuth tokens are found.")
    # Attempt to start services that might have stored tokens (e.g., Twitch)
    # They will check tokens internally and connect if valid/refreshed.
    initial_start_tasks = [
        handle_service_control(ServiceControl(service_name="twitch", command="start")),
        handle_service_control(ServiceControl(service_name="youtube", command="start")),
        handle_service_control(ServiceControl(service_name="x", command="start")),
        # Don't auto-start Whatnot bridge usually
    ]
    await asyncio.gather(*initial_start_tasks, return_exceptions=True)
    logger.info("--- Application startup complete. Running! ---")

    yield # App runs

    logger.info("--- Application shutdown sequence initiated ---")
    logger.info("Stopping platform services (sending stop commands)...");
    stop_tasks = [
        handle_service_control(ServiceControl(service_name=name, command="stop"))
        for name in service_control_map.keys()
    ]
    await asyncio.gather(*stop_tasks, return_exceptions=True)

    logger.info("Waiting briefly..."); await asyncio.sleep(2);
    logger.info("Stopping event bus worker..."); await event_bus.stop()

    # Final check for lingering tasks (should be handled by stop commands now)
    if background_tasks:
        logger.warning(f"Attempting final cancellation for {len(background_tasks)} lingering background tasks...")
        for task in list(background_tasks):
            if task and not task.done(): task.cancel()
        try:
            await asyncio.wait_for(asyncio.gather(*background_tasks, return_exceptions=True), timeout=5.0)
            logger.debug("Gathered cancelled background tasks successfully.")
        except asyncio.TimeoutError: logger.error("Timeout waiting for background tasks to cancel.")
        except Exception as e: logger.exception(f"Error during final gathering of cancelled tasks: {e}")
    else: logger.info("No lingering background tasks found during shutdown.")
    logger.info("--- Application shutdown complete. ---")


# --- FastAPI App Creation ---
app = FastAPI(
    title="FoSBot (OAuth Config)",
    version="0.4.0-oauth", # Updated version
    lifespan=lifespan
)

# --- Mount Routers ---
app.include_router(auth_api.router) # Add the Auth router
app.include_router(ws_endpoints.router, prefix="/ws")
app.include_router(settings_api.router, prefix="/api", tags=["Settings & Control"])

# --- Mount Static Files ---
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

# --- Direct Run (Debugging Only) ---
if __name__ == "__main__":
    import uvicorn
    from app.core.config import WS_HOST, WS_PORT, LOG_LEVEL
    logger.warning("Running via main.py is intended for debugging ONLY.")
    uvicorn.run("app.main:app", host=WS_HOST, port=WS_PORT, log_level=LOG_LEVEL.lower(), reload=True) # Enable reload for dev
# --- File: app/main.py --- END ---