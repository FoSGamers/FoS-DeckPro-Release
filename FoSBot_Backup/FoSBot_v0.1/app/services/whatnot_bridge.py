import logging; logger=logging.getLogger(__name__); import asyncio; from app.core.event_bus import event_bus; from app.events import PlatformStatusUpdate
# This service would likely manage the pool of WS connections from the extension
# For now, it's just a placeholder task
async def run_whatnot_bridge(): event_bus.publish(PlatformStatusUpdate(platform='whatnot', status='disabled', message='Bridge not active')); logger.warning("Whatnot Bridge service NOT IMPLEMENTED."); await asyncio.sleep(3600*24)
async def stop_whatnot_bridge(): logger.info("Whatnot Bridge stop called (stub).")
def start_whatnot_bridge_task(): logger.info("Whatnot Bridge start called (stub)."); return None
