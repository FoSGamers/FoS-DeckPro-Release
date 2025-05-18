from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime
import threading
import time
import logging
import json
from pathlib import Path
from dataclasses import dataclass
from enum import Enum
import uuid
import queue
import asyncio
from concurrent.futures import ThreadPoolExecutor
import psutil
import signal
import sys
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class StateType(Enum):
    APPLICATION = "application"
    UI = "ui"
    DATA = "data"
    SYSTEM = "system"
    USER = "user"
    SESSION = "session"

class StateTransition(Enum):
    INITIALIZE = "initialize"
    LOAD = "load"
    SAVE = "save"
    UPDATE = "update"
    RESET = "reset"
    CLEAR = "clear"
    MERGE = "merge"
    SPLIT = "split"

@dataclass
class State:
    id: str
    type: StateType
    data: Dict[str, Any]
    timestamp: datetime
    version: str
    parent_id: Optional[str] = None
    metadata: Dict[str, Any] = None

class StateManager(QObject):
    state_changed = Signal(str, State)  # state_id, new_state
    state_transition = Signal(str, StateTransition)  # state_id, transition
    state_error = Signal(str, str)  # state_id, error_message
    
    def __init__(self):
        super().__init__()
        self.states: Dict[str, State] = {}
        self.state_history: Dict[str, List[State]] = {}
        self.state_listeners: Dict[str, List[Callable]] = {}
        self.transition_handlers: Dict[StateTransition, List[Callable]] = {}
        self._setup_logging()
        self._setup_directories()
        self._load_states()
        self._setup_transition_handlers()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("state")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        log_file = Path("logs") / "state.log"
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup necessary directories"""
        self.states_dir = Path("states")
        self.states_dir.mkdir(exist_ok=True)
        
    def _load_states(self):
        """Load saved states from disk"""
        try:
            states_file = self.states_dir / "states.json"
            if states_file.exists():
                with open(states_file, 'r') as f:
                    states_data = json.load(f)
                    for state_data in states_data:
                        state = self._create_state_from_data(state_data)
                        self.states[state.id] = state
                        self.state_history[state.id] = []
        except Exception as e:
            self.logger.error(f"Error loading states: {e}")
            
    def _save_states(self):
        """Save states to disk"""
        try:
            states_file = self.states_dir / "states.json"
            states_data = []
            for state in self.states.values():
                state_data = {
                    "id": state.id,
                    "type": state.type.value,
                    "data": state.data,
                    "timestamp": state.timestamp.isoformat(),
                    "version": state.version,
                    "parent_id": state.parent_id,
                    "metadata": state.metadata
                }
                states_data.append(state_data)
                
            with open(states_file, 'w') as f:
                json.dump(states_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving states: {e}")
            
    def _setup_transition_handlers(self):
        """Setup handlers for state transitions"""
        self.transition_handlers = {
            StateTransition.INITIALIZE: [self._handle_initialize],
            StateTransition.LOAD: [self._handle_load],
            StateTransition.SAVE: [self._handle_save],
            StateTransition.UPDATE: [self._handle_update],
            StateTransition.RESET: [self._handle_reset],
            StateTransition.CLEAR: [self._handle_clear],
            StateTransition.MERGE: [self._handle_merge],
            StateTransition.SPLIT: [self._handle_split]
        }
        
    def create_state(self, type: StateType, data: Dict[str, Any],
                    parent_id: Optional[str] = None,
                    metadata: Dict[str, Any] = None) -> str:
        """Create a new state"""
        state_id = str(uuid.uuid4())
        state = State(
            id=state_id,
            type=type,
            data=data,
            timestamp=datetime.now(),
            version="1.0.0",
            parent_id=parent_id,
            metadata=metadata or {}
        )
        
        self.states[state_id] = state
        self.state_history[state_id] = []
        self._save_states()
        
        # Emit signal
        self.state_changed.emit(state_id, state)
        
        return state_id
        
    def get_state(self, state_id: str) -> Optional[State]:
        """Get state by ID"""
        return self.states.get(state_id)
        
    def get_states(self, type: StateType = None) -> List[State]:
        """Get all states, optionally filtered by type"""
        if type:
            return [s for s in self.states.values() if s.type == type]
        return list(self.states.values())
        
    def update_state(self, state_id: str, data: Dict[str, Any],
                    transition: StateTransition = StateTransition.UPDATE) -> bool:
        """Update a state"""
        if state_id in self.states:
            # Store current state in history
            current_state = self.states[state_id]
            self.state_history[state_id].append(current_state)
            
            # Create new state
            new_state = State(
                id=state_id,
                type=current_state.type,
                data=data,
                timestamp=datetime.now(),
                version=self._increment_version(current_state.version),
                parent_id=current_state.id,
                metadata=current_state.metadata
            )
            
            # Update state
            self.states[state_id] = new_state
            self._save_states()
            
            # Emit signals
            self.state_transition.emit(state_id, transition)
            self.state_changed.emit(state_id, new_state)
            
            return True
        return False
        
    def delete_state(self, state_id: str) -> bool:
        """Delete a state"""
        if state_id in self.states:
            del self.states[state_id]
            del self.state_history[state_id]
            self._save_states()
            return True
        return False
        
    def register_listener(self, state_id: str, listener: Callable):
        """Register a state change listener"""
        if state_id not in self.state_listeners:
            self.state_listeners[state_id] = []
        self.state_listeners[state_id].append(listener)
        
    def unregister_listener(self, state_id: str, listener: Callable):
        """Unregister a state change listener"""
        if state_id in self.state_listeners:
            self.state_listeners[state_id].remove(listener)
            
    def get_state_history(self, state_id: str) -> List[State]:
        """Get state history"""
        return self.state_history.get(state_id, [])
        
    def revert_state(self, state_id: str, version: str = None) -> bool:
        """Revert state to a previous version"""
        if state_id in self.state_history:
            history = self.state_history[state_id]
            if version:
                # Find state with specific version
                for state in reversed(history):
                    if state.version == version:
                        self.states[state_id] = state
                        self._save_states()
                        self.state_changed.emit(state_id, state)
                        return True
            else:
                # Revert to last state
                if history:
                    self.states[state_id] = history[-1]
                    self._save_states()
                    self.state_changed.emit(state_id, history[-1])
                    return True
        return False
        
    def _increment_version(self, version: str) -> str:
        """Increment version number"""
        major, minor, patch = map(int, version.split('.'))
        return f"{major}.{minor}.{patch + 1}"
        
    def _create_state_from_data(self, data: Dict[str, Any]) -> State:
        """Create a state from saved data"""
        return State(
            id=data["id"],
            type=StateType(data["type"]),
            data=data["data"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            version=data["version"],
            parent_id=data["parent_id"],
            metadata=data["metadata"]
        )
        
    # Transition Handlers
    def _handle_initialize(self, state_id: str, data: Dict[str, Any]):
        """Handle state initialization"""
        pass
        
    def _handle_load(self, state_id: str, data: Dict[str, Any]):
        """Handle state loading"""
        pass
        
    def _handle_save(self, state_id: str, data: Dict[str, Any]):
        """Handle state saving"""
        pass
        
    def _handle_update(self, state_id: str, data: Dict[str, Any]):
        """Handle state update"""
        pass
        
    def _handle_reset(self, state_id: str, data: Dict[str, Any]):
        """Handle state reset"""
        pass
        
    def _handle_clear(self, state_id: str, data: Dict[str, Any]):
        """Handle state clear"""
        pass
        
    def _handle_merge(self, state_id: str, data: Dict[str, Any]):
        """Handle state merge"""
        pass
        
    def _handle_split(self, state_id: str, data: Dict[str, Any]):
        """Handle state split"""
        pass 