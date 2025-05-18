import logging; logger=logging.getLogger(__name__); import asyncio; from app.core.event_bus import event_bus; from app.events import PlatformStatusUpdate
async def run_youtube_service(): event_bus.publish(PlatformStatusUpdate(platform='youtube', status='disabled', message='Not implemented')); logger.warning("YouTube service NOT IMPLEMENTED."); await asyncio.sleep(3600*24) # Sleep long time
async def stop_youtube_service(): logger.info("YouTube service stop called (stub).")
def start_youtube_service_task(): logger.info("YouTube service start called (stub)."); return None # Return None as no task created
