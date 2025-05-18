import asyncio
import logging
import sys # Import sys for exception info depth
from collections import defaultdict
from typing import Type, Callable, Dict, List, TypeVar, Coroutine, Any
# Ensure events.py is correctly located relative to core
from app.events import Event

logger = logging.getLogger(__name__)
T = TypeVar('T', bound=Event) # Type variable for events

class AsyncEventBus:
    def __init__(self):
        # Stores listeners: {EventType: [handler1, handler2, ...]}
        self._listeners: Dict[Type[Event], List[Callable[[T], Coroutine[Any, Any, None]]]] = defaultdict(list)
        # Set a max size for the queue to prevent unbounded memory growth if processing lags
        self._queue: asyncio.Queue = asyncio.Queue(maxsize=1000) # Adjust size as needed
        self._worker_task: asyncio.Task | None = None
        self._running = False # Flag to control the processing loop

    def subscribe(self, event_type: Type[T], handler: Callable[[T], Coroutine[Any, Any, None]]):
        """Subscribe an async handler to an event type."""
        # Ensure handler is actually an async function
        if not asyncio.iscoroutinefunction(handler):
            raise TypeError(f"Handler {getattr(handler, '__name__', repr(handler))} must be an async function (coroutine)")
        self._listeners[event_type].append(handler)
        logger.debug(f"Handler '{getattr(handler, '__name__', repr(handler))}' subscribed to {event_type.__name__}")

    def publish(self, event: Event):
        """Publish an event to the queue for async processing."""
        if not self._running:
            logger.warning(f"Event bus not running, discarding event: {type(event).__name__}")
            return
        try:
            # Use put_nowait to avoid blocking the publisher if queue is full
            self._queue.put_nowait(event)
            logger.debug(f"Event {type(event).__name__} published to queue (qsize: {self._queue.qsize()}).")
        except asyncio.QueueFull:
            # Log loudly if the queue is full, as events will be dropped
            logger.error(f"Event bus queue is FULL (maxsize={self._queue.maxsize})! Discarding event: {type(event).__name__}. "
                         f"Consider increasing queue size or ensuring event handlers are processing quickly enough.")

    async def _process_events(self):
        """Worker coroutine that processes events from the queue."""
        logger.info("Event bus processor task started.")
        # --- CORRECTED INDENTATION ---
        while self._running: # Loop continues as long as the running flag is True
            try:
                # Wait for an event from the queue
                event = await self._queue.get()

                # Handle potential sentinel value used during shutdown
                if event is None:
                    logger.debug("Received None sentinel, continuing shutdown check.")
                    continue # Go back to check self._running

                event_type = type(event)
                logger.debug(f"Processing event {event_type.__name__} from queue (qsize: {self._queue.qsize()}).")

                # Find all handlers for this event type (including handlers for parent classes)
                handlers_to_call = []
                for registered_type, handlers in self._listeners.items():
                    if isinstance(event, registered_type):
                        handlers_to_call.extend(handlers)

                if not handlers_to_call:
                    logger.debug(f"No listeners found for event type {event_type.__name__}")
                    self._queue.task_done() # Mark item as done even if no listeners
                    continue # Process next item

                # Execute all handlers concurrently using asyncio.gather
                # Name tasks for better debugging
                tasks = [
                    asyncio.create_task(
                        handler(event),
                        name=f"event_handler_{getattr(handler, '__name__', f'unknown_{id(handler)}')}_{event_type.__name__}"
                    )
                    for handler in handlers_to_call
                ]
                results = await asyncio.gather(*tasks, return_exceptions=True)

                # Log any exceptions that occurred within the handlers
                for i, result in enumerate(results):
                    if isinstance(result, Exception):
                        handler_name = getattr(handlers_to_call[i], '__name__', repr(handlers_to_call[i]))
                        # Log traceback only if log level is DEBUG for clarity
                        log_traceback = logger.isEnabledFor(logging.DEBUG)
                        logger.error(f"Exception in handler '{handler_name}' for event {event_type.__name__}: {result}", exc_info=log_traceback)

                self._queue.task_done() # Signal that this event has been processed

            except asyncio.CancelledError:
                # This happens when self.stop() is called
                logger.info("Event bus processing task cancelled.")
                break # Exit the while loop
            except Exception as e:
                # Catch-all for unexpected errors in the processing loop itself
                logger.exception(f"Unexpected error in event processing loop: {e}")
                # Avoid spinning on persistent errors; wait before retrying
                await asyncio.sleep(1)
        # --- END INDENTATION CORRECTION ---
        logger.info("Event bus processor task stopped.")

    async def start(self):
        """Start the background event processing worker."""
        if self._running:
            logger.warning("Event bus already running.")
            return
        self._running = True
        # Create the task with a descriptive name
        self._worker_task = asyncio.create_task(self._process_events(), name="EventBusProcessor")
        logger.info("Event bus started.")

    async def stop(self):
        """Stop the background event processing worker gracefully."""
        if not self._running or not self._worker_task or self._worker_task.done():
            logger.info("Event bus already stopped or was never started.")
            return

        logger.info("Stopping event bus worker...")
        self._running = False # Signal the loop to stop processing new items

        # Add a sentinel to potentially unblock the worker if it's waiting on an empty queue
        try:
            self._queue.put_nowait(None)
        except asyncio.QueueFull:
             logger.warning("Event queue full during shutdown initiation.")
             # Shutdown will still proceed when worker is cancelled

        # Cancel the worker task
        if not self._worker_task.done():
             self._worker_task.cancel()

        # Wait for the task to finish (handles CancelledError internally)
        try:
            await self._worker_task
            logger.info("Event bus worker stopped successfully.")
        except asyncio.CancelledError:
            # This is expected when we cancel it
            logger.info("Event bus worker stop confirmed (was cancelled).")
        except Exception as e:
             # Log any other error during shutdown wait
             logger.exception(f"Error during event bus worker shutdown wait: {e}")
        finally:
             self._worker_task = None # Clear task reference

# Create a single global instance (can be replaced with DI later if needed)
event_bus = AsyncEventBus()