# Version History: 0.7.2 -> 0.7.3
import asyncio
import logging
from typing import Any, Callable, Type, Dict, List
from collections import defaultdict

logger = logging.getLogger(__name__)

class EventBus:
    def __init__(self):
        self._handlers: Dict[Type[Any], List[Callable[[Any], None]]] = defaultdict(list)
        self._queue = asyncio.Queue()
        self._running = False
        self._task = None

    def subscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        """Subscribe a handler to an event type."""
        self._handlers[event_type].append(handler)
        logger.debug(f"Handler '{handler.__name__}' subscribed to {event_type.__name__}")

    def unsubscribe(self, event_type: Type[Any], handler: Callable[[Any], None]) -> None:
        """Unsubscribe a handler from an event type."""
        if handler in self._handlers[event_type]:
            self._handlers[event_type].remove(handler)
            logger.debug(f"Handler '{handler.__name__}' unsubscribed from {event_type.__name__}")

    def publish(self, event: Any) -> None:
        """Publish an event to the queue."""
        self._queue.put_nowait(event)
        logger.debug(f"Event {type(event).__name__} published (qsize: {self._queue.qsize()}).")

    async def start(self):
        """Start the event bus processor."""
        if not self._running:
            self._running = True
            self._task = asyncio.create_task(self._process_events(), name="EventBusProcessor")
            logger.info("Event bus processor task started.")

    async def stop(self):
        """Stop the event bus processor."""
        if self._running:
            self._running = False
            if self._task and not self._task.done():
                self._task.cancel()
                try:
                    await self._task
                    logger.info("Event bus processor task stopped.")
                except asyncio.CancelledError:
                    logger.info("Event bus processing task cancelled.")
            self._task = None

    async def _process_events(self):
        """Process events from the queue."""
        logger.info("Event bus started.")
        while self._running:
            try:
                event = await asyncio.wait_for(self._queue.get(), timeout=1.0)
                logger.debug(f"Processing event {type(event).__name__} from queue (qsize: {self._queue.qsize()}).")
                for event_type in self._handlers:
                    if isinstance(event, event_type):
                        for handler in self._handlers[event_type]:
                            try:
                                await handler(event)
                                logger.debug(f"Handler '{handler.__name__}' processed {type(event).__name__}")
                            except Exception as e:
                                logger.error(f"Error in handler '{handler.__name__}' for {type(event).__name__}: {e}", exc_info=True)
                self._queue.task_done()
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                logger.info("Event bus processing task cancelled.")
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}", exc_info=True)

event_bus = EventBus()

