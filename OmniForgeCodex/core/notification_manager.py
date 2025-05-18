from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
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
from PySide6.QtWidgets import QSystemTrayIcon, QMenu
from PySide6.QtGui import QAction

class NotificationPriority(Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3

class NotificationType(Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"
    USER = "user"
    EVENT = "event"

class NotificationStatus(Enum):
    PENDING = "pending"
    DISPLAYED = "displayed"
    ACKNOWLEDGED = "acknowledged"
    EXPIRED = "expired"
    CANCELLED = "cancelled"

@dataclass
class Notification:
    id: str
    title: str
    message: str
    type: NotificationType
    priority: NotificationPriority
    status: NotificationStatus
    source: str
    timestamp: datetime
    expiry: Optional[datetime] = None
    actions: List[Dict[str, Any]] = None
    metadata: Dict[str, Any] = None

class NotificationManager(QObject):
    notification_received = Signal(Notification)
    notification_acknowledged = Signal(str)  # notification_id
    notification_expired = Signal(str)  # notification_id
    
    def __init__(self):
        super().__init__()
        self.notifications: Dict[str, Notification] = {}
        self.notification_queue = queue.PriorityQueue()
        self.event_handlers: Dict[str, List[Callable]] = {}
        self._setup_logging()
        self._setup_directories()
        self._setup_system_tray()
        self._load_notifications()
        self._start_notification_processor()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("notification")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        log_file = Path("logs") / "notifications.log"
        log_file.parent.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup necessary directories"""
        self.notifications_dir = Path("notifications")
        self.notifications_dir.mkdir(exist_ok=True)
        
    def _setup_system_tray(self):
        """Setup system tray icon and menu"""
        self.tray_icon = QSystemTrayIcon()
        self.tray_icon.setIcon(QIcon(":/icons/app.png"))
        
        # Create tray menu
        self.tray_menu = QMenu()
        
        # Add notification actions
        self.show_notifications_action = QAction("Show Notifications", self)
        self.show_notifications_action.triggered.connect(self.show_notifications)
        self.tray_menu.addAction(self.show_notifications_action)
        
        self.clear_notifications_action = QAction("Clear All", self)
        self.clear_notifications_action.triggered.connect(self.clear_notifications)
        self.tray_menu.addAction(self.clear_notifications_action)
        
        self.tray_menu.addSeparator()
        
        # Add system actions
        self.quit_action = QAction("Quit", self)
        self.quit_action.triggered.connect(QApplication.quit)
        self.tray_menu.addAction(self.quit_action)
        
        self.tray_icon.setContextMenu(self.tray_menu)
        self.tray_icon.show()
        
    def _load_notifications(self):
        """Load saved notifications from disk"""
        try:
            notifications_file = self.notifications_dir / "notifications.json"
            if notifications_file.exists():
                with open(notifications_file, 'r') as f:
                    notifications_data = json.load(f)
                    for notification_data in notifications_data:
                        notification = self._create_notification_from_data(notification_data)
                        self.notifications[notification.id] = notification
        except Exception as e:
            self.logger.error(f"Error loading notifications: {e}")
            
    def _save_notifications(self):
        """Save notifications to disk"""
        try:
            notifications_file = self.notifications_dir / "notifications.json"
            notifications_data = []
            for notification in self.notifications.values():
                notification_data = {
                    "id": notification.id,
                    "title": notification.title,
                    "message": notification.message,
                    "type": notification.type.value,
                    "priority": notification.priority.value,
                    "status": notification.status.value,
                    "source": notification.source,
                    "timestamp": notification.timestamp.isoformat(),
                    "expiry": notification.expiry.isoformat() if notification.expiry else None,
                    "actions": notification.actions,
                    "metadata": notification.metadata
                }
                notifications_data.append(notification_data)
                
            with open(notifications_file, 'w') as f:
                json.dump(notifications_data, f, indent=2)
                
        except Exception as e:
            self.logger.error(f"Error saving notifications: {e}")
            
    def _start_notification_processor(self):
        """Start the notification processing thread"""
        def process_notifications():
            while True:
                try:
                    priority, notification = self.notification_queue.get_nowait()
                    self._display_notification(notification)
                except queue.Empty:
                    time.sleep(0.1)
                    
        self.processor_thread = threading.Thread(target=process_notifications, daemon=True)
        self.processor_thread.start()
        
    def add_notification(self, title: str, message: str, type: NotificationType,
                        priority: NotificationPriority, source: str,
                        expiry: Optional[datetime] = None,
                        actions: List[Dict[str, Any]] = None,
                        metadata: Dict[str, Any] = None) -> str:
        """Add a new notification"""
        notification_id = str(uuid.uuid4())
        notification = Notification(
            id=notification_id,
            title=title,
            message=message,
            type=type,
            priority=priority,
            status=NotificationStatus.PENDING,
            source=source,
            timestamp=datetime.now(),
            expiry=expiry,
            actions=actions or [],
            metadata=metadata or {}
        )
        
        self.notifications[notification_id] = notification
        self.notification_queue.put((priority.value, notification))
        self._save_notifications()
        
        # Emit signal
        self.notification_received.emit(notification)
        
        return notification_id
        
    def remove_notification(self, notification_id: str) -> bool:
        """Remove a notification"""
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            notification.status = NotificationStatus.CANCELLED
            del self.notifications[notification_id]
            self._save_notifications()
            return True
        return False
        
    def acknowledge_notification(self, notification_id: str) -> bool:
        """Acknowledge a notification"""
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            notification.status = NotificationStatus.ACKNOWLEDGED
            self._save_notifications()
            self.notification_acknowledged.emit(notification_id)
            return True
        return False
        
    def clear_notifications(self):
        """Clear all notifications"""
        self.notifications.clear()
        self._save_notifications()
        
    def get_notifications(self, status: NotificationStatus = None) -> List[Notification]:
        """Get all notifications, optionally filtered by status"""
        if status:
            return [n for n in self.notifications.values() if n.status == status]
        return list(self.notifications.values())
        
    def register_event_handler(self, event_type: str, handler: Callable):
        """Register an event handler"""
        if event_type not in self.event_handlers:
            self.event_handlers[event_type] = []
        self.event_handlers[event_type].append(handler)
        
    def unregister_event_handler(self, event_type: str, handler: Callable):
        """Unregister an event handler"""
        if event_type in self.event_handlers:
            self.event_handlers[event_type].remove(handler)
            
    def trigger_event(self, event_type: str, data: Dict[str, Any] = None):
        """Trigger an event"""
        if event_type in self.event_handlers:
            for handler in self.event_handlers[event_type]:
                try:
                    handler(data)
                except Exception as e:
                    self.logger.error(f"Error in event handler {handler.__name__}: {e}")
                    
    def _display_notification(self, notification: Notification):
        """Display a notification"""
        try:
            # Update status
            notification.status = NotificationStatus.DISPLAYED
            
            # Show system tray notification
            self.tray_icon.showMessage(
                notification.title,
                notification.message,
                self._get_notification_icon(notification.type),
                5000  # 5 seconds
            )
            
            # Check for expiry
            if notification.expiry:
                QTimer.singleShot(
                    int((notification.expiry - datetime.now()).total_seconds() * 1000),
                    lambda: self._expire_notification(notification.id)
                )
                
        except Exception as e:
            self.logger.error(f"Error displaying notification: {e}")
            
    def _expire_notification(self, notification_id: str):
        """Expire a notification"""
        if notification_id in self.notifications:
            notification = self.notifications[notification_id]
            notification.status = NotificationStatus.EXPIRED
            self._save_notifications()
            self.notification_expired.emit(notification_id)
            
    def _get_notification_icon(self, type: NotificationType) -> QSystemTrayIcon.MessageIcon:
        """Get the appropriate icon for a notification type"""
        icon_map = {
            NotificationType.INFO: QSystemTrayIcon.Information,
            NotificationType.SUCCESS: QSystemTrayIcon.Information,
            NotificationType.WARNING: QSystemTrayIcon.Warning,
            NotificationType.ERROR: QSystemTrayIcon.Critical,
            NotificationType.SYSTEM: QSystemTrayIcon.Information,
            NotificationType.USER: QSystemTrayIcon.Information,
            NotificationType.EVENT: QSystemTrayIcon.Information
        }
        return icon_map.get(type, QSystemTrayIcon.Information)
        
    def _create_notification_from_data(self, data: Dict[str, Any]) -> Notification:
        """Create a notification from saved data"""
        return Notification(
            id=data["id"],
            title=data["title"],
            message=data["message"],
            type=NotificationType(data["type"]),
            priority=NotificationPriority(data["priority"]),
            status=NotificationStatus(data["status"]),
            source=data["source"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            expiry=datetime.fromisoformat(data["expiry"]) if data["expiry"] else None,
            actions=data["actions"],
            metadata=data["metadata"]
        ) 