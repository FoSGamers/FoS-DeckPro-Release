from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass
from enum import Enum, auto
import logging
from queue import PriorityQueue
import threading

class EventPriority(Enum):
    """Event priority levels"""
    LOW = auto()
    NORMAL = auto()
    HIGH = auto()
    CRITICAL = auto()

@dataclass
class Event:
    """Represents an event with data and priority"""
    name: str
    data: Any
    priority: EventPriority = EventPriority.NORMAL
    source: Optional[str] = None

class EventSystem:
    """Manages event handling with prioritization and async support"""
    
    def __init__(self):
        self.logger = logging.getLogger("event_system")
        self.handlers: Dict[str, List[Callable]] = {}
        self.event_queue = PriorityQueue()
        self.running = False
        self.worker_thread = None
        self.lock = threading.Lock()
    
    def start(self) -> None:
        """Start the event system"""
        if not self.running:
            self.running = True
            self.worker_thread = threading.Thread(target=self._process_events)
            self.worker_thread.daemon = True
            self.worker_thread.start()
            self.logger.info("Event system started")
    
    def stop(self) -> None:
        """Stop the event system"""
        if self.running:
            self.running = False
            if self.worker_thread:
                self.worker_thread.join()
            self.logger.info("Event system stopped")
    
    def register_handler(self, event_name: str, handler: Callable) -> None:
        """Register an event handler"""
        with self.lock:
            if event_name not in self.handlers:
                self.handlers[event_name] = []
            self.handlers[event_name].append(handler)
            self.logger.debug(f"Registered handler for event: {event_name}")
    
    def unregister_handler(self, event_name: str, handler: Callable) -> None:
        """Unregister an event handler"""
        with self.lock:
            if event_name in self.handlers:
                self.handlers[event_name].remove(handler)
                if not self.handlers[event_name]:
                    del self.handlers[event_name]
                self.logger.debug(f"Unregistered handler for event: {event_name}")
    
    def emit(self, event: Event) -> None:
        """Emit an event"""
        if not self.running:
            self.logger.warning("Event system not running, event will be queued")
        
        # Calculate priority value (lower is higher priority)
        priority_value = {
            EventPriority.CRITICAL: 0,
            EventPriority.HIGH: 1,
            EventPriority.NORMAL: 2,
            EventPriority.LOW: 3
        }[event.priority]
        
        self.event_queue.put((priority_value, event))
        self.logger.debug(f"Emitted event: {event.name} (priority: {event.priority})")
    
    def _process_events(self) -> None:
        """Process events from the queue"""
        while self.running:
            try:
                priority, event = self.event_queue.get(timeout=1)
                self._handle_event(event)
            except Exception as e:
                self.logger.error(f"Error processing event: {str(e)}")
    
    def _handle_event(self, event: Event) -> None:
        """Handle a single event"""
        try:
            handlers = self.handlers.get(event.name, [])
            for handler in handlers:
                try:
                    handler(event)
                except Exception as e:
                    self.logger.error(f"Error in event handler for {event.name}: {str(e)}")
        except Exception as e:
            self.logger.error(f"Error handling event {event.name}: {str(e)}")
    
    def clear_handlers(self) -> None:
        """Clear all event handlers"""
        with self.lock:
            self.handlers.clear()
            self.logger.info("Cleared all event handlers")
    
    def get_handler_count(self, event_name: str) -> int:
        """Get the number of handlers for an event"""
        return len(self.handlers.get(event_name, [])) 