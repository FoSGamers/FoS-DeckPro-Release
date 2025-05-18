from threading import Lock, RLock, Event
from typing import Dict, Any
import time

class ConcurrencyManager:
    def __init__(self):
        self._locks: Dict[str, RLock] = {}
        self._events: Dict[str, Event] = {}
        self._resources: Dict[str, Any] = {}
        
    def get_lock(self, resource_id: str) -> RLock:
        """Get or create a lock for a resource"""
        if resource_id not in self._locks:
            self._locks[resource_id] = RLock()
        return self._locks[resource_id]
        
    def get_event(self, event_id: str) -> Event:
        """Get or create an event"""
        if event_id not in self._events:
            self._events[event_id] = Event()
        return self._events[event_id]
        
    @contextmanager
    def acquire_resource(self, resource_id: str, timeout: float = None):
        """Context manager for resource acquisition"""
        lock = self.get_lock(resource_id)
        if lock.acquire(timeout=timeout):
            try:
                yield
            finally:
                lock.release()
        else:
            raise TimeoutError(f"Could not acquire resource {resource_id}")
            
    def wait_for_event(self, event_id: str, timeout: float = None) -> bool:
        """Wait for an event to be set"""
        event = self.get_event(event_id)
        return event.wait(timeout=timeout)
        
    def set_event(self, event_id: str):
        """Set an event"""
        event = self.get_event(event_id)
        event.set()
        
    def clear_event(self, event_id: str):
        """Clear an event"""
        event = self.get_event(event_id)
        event.clear() 