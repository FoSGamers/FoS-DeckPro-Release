from typing import Dict, Any, List, Optional, Union, Tuple, Callable
from datetime import datetime, timedelta
import threading
import time
import logging
import json
from pathlib import Path
import socket
import requests
import urllib3
import ssl
import asyncio
import aiohttp
from dataclasses import dataclass
from enum import Enum
import uuid
import queue
from concurrent.futures import ThreadPoolExecutor
from PySide6.QtCore import QObject, Signal, Slot, QTimer

class NetworkProtocol(Enum):
    HTTP = "http"
    HTTPS = "https"
    WS = "ws"
    WSS = "wss"
    TCP = "tcp"
    UDP = "udp"

class ConnectionState(Enum):
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    DISCONNECTING = "disconnecting"
    ERROR = "error"

@dataclass
class ConnectionInfo:
    id: str
    protocol: NetworkProtocol
    host: str
    port: int
    state: ConnectionState
    start_time: datetime
    last_activity: datetime
    bytes_sent: int
    bytes_received: int
    latency: float
    error_count: int
    ssl_enabled: bool
    timeout: float
    retry_count: int
    max_retries: int
    retry_delay: float

class NetworkManager(QObject):
    connection_state_changed = Signal(str, ConnectionState)  # connection_id, new_state
    connection_error = Signal(str, str)  # connection_id, error_message
    data_received = Signal(str, bytes)  # connection_id, data
    data_sent = Signal(str, bytes)  # connection_id, data
    
    def __init__(self):
        super().__init__()
        self.log_dir = Path("logs")
        self.network_log = self.log_dir / "network.log"
        
        # Connection tracking
        self.connections: Dict[str, ConnectionInfo] = {}
        self.connection_history: List[ConnectionInfo] = []
        self.connection_queue = queue.PriorityQueue()
        
        # Network settings
        self.max_connections = 100
        self.connection_timeout = 30
        self.retry_delay = 1.0
        self.max_retries = 3
        self.keep_alive_interval = 60
        self.cleanup_interval = 300
        
        # SSL settings
        self.ssl_context = ssl.create_default_context()
        self.ssl_verify = True
        self.ssl_cert_file = None
        self.ssl_key_file = None
        
        # Setup
        self._setup_logging()
        self._setup_directories()
        self._start_connection_monitoring()
        self._start_connection_cleanup()
        
    def _setup_logging(self):
        """Setup logging configuration"""
        self.logger = logging.getLogger("network")
        self.logger.setLevel(logging.INFO)
        
        # Add file handler
        self.log_dir.mkdir(exist_ok=True)
        file_handler = logging.FileHandler(self.network_log)
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        self.logger.addHandler(file_handler)
        
    def _setup_directories(self):
        """Setup necessary directories"""
        self.log_dir.mkdir(exist_ok=True)
        
    def _start_connection_monitoring(self):
        """Start connection monitoring"""
        def monitor():
            while True:
                self._check_connections()
                time.sleep(1)
                
        self.monitor_thread = threading.Thread(target=monitor, daemon=True)
        self.monitor_thread.start()
        
    def _start_connection_cleanup(self):
        """Start connection cleanup"""
        def cleanup():
            while True:
                self._cleanup_connections()
                time.sleep(self.cleanup_interval)
                
        self.cleanup_thread = threading.Thread(target=cleanup, daemon=True)
        self.cleanup_thread.start()
        
    async def connect(self, protocol: NetworkProtocol, host: str, port: int,
                     ssl_enabled: bool = False, timeout: float = None) -> Optional[str]:
        """Establish a new connection"""
        try:
            # Create connection info
            connection_id = str(uuid.uuid4())
            connection_info = ConnectionInfo(
                id=connection_id,
                protocol=protocol,
                host=host,
                port=port,
                state=ConnectionState.CONNECTING,
                start_time=datetime.now(),
                last_activity=datetime.now(),
                bytes_sent=0,
                bytes_received=0,
                latency=0.0,
                error_count=0,
                ssl_enabled=ssl_enabled,
                timeout=timeout or self.connection_timeout,
                retry_count=0,
                max_retries=self.max_retries,
                retry_delay=self.retry_delay
            )
            
            # Add to tracking
            self.connections[connection_id] = connection_info
            self.connection_history.append(connection_info)
            
            # Establish connection
            if protocol in [NetworkProtocol.HTTP, NetworkProtocol.HTTPS]:
                await self._connect_http(connection_info)
            elif protocol in [NetworkProtocol.WS, NetworkProtocol.WSS]:
                await self._connect_websocket(connection_info)
            elif protocol in [NetworkProtocol.TCP, NetworkProtocol.UDP]:
                await self._connect_socket(connection_info)
                
            # Update state
            connection_info.state = ConnectionState.CONNECTED
            self.connection_state_changed.emit(connection_id, ConnectionState.CONNECTED)
            
            return connection_id
            
        except Exception as e:
            self.logger.error(f"Error establishing connection: {e}")
            if connection_id in self.connections:
                self.connections[connection_id].state = ConnectionState.ERROR
                self.connection_error.emit(connection_id, str(e))
            return None
            
    async def disconnect(self, connection_id: str) -> bool:
        """Close a connection"""
        try:
            if connection_id in self.connections:
                connection_info = self.connections[connection_id]
                
                # Update state
                connection_info.state = ConnectionState.DISCONNECTING
                self.connection_state_changed.emit(connection_id, ConnectionState.DISCONNECTING)
                
                # Close connection
                if connection_info.protocol in [NetworkProtocol.HTTP, NetworkProtocol.HTTPS]:
                    await self._disconnect_http(connection_info)
                elif connection_info.protocol in [NetworkProtocol.WS, NetworkProtocol.WSS]:
                    await self._disconnect_websocket(connection_info)
                elif connection_info.protocol in [NetworkProtocol.TCP, NetworkProtocol.UDP]:
                    await self._disconnect_socket(connection_info)
                    
                # Update state
                connection_info.state = ConnectionState.DISCONNECTED
                self.connection_state_changed.emit(connection_id, ConnectionState.DISCONNECTED)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error closing connection: {e}")
            
        return False
        
    async def send_data(self, connection_id: str, data: bytes) -> bool:
        """Send data through a connection"""
        try:
            if connection_id in self.connections:
                connection_info = self.connections[connection_id]
                
                # Send data
                if connection_info.protocol in [NetworkProtocol.HTTP, NetworkProtocol.HTTPS]:
                    await self._send_http(connection_info, data)
                elif connection_info.protocol in [NetworkProtocol.WS, NetworkProtocol.WSS]:
                    await self._send_websocket(connection_info, data)
                elif connection_info.protocol in [NetworkProtocol.TCP, NetworkProtocol.UDP]:
                    await self._send_socket(connection_info, data)
                    
                # Update stats
                connection_info.bytes_sent += len(data)
                connection_info.last_activity = datetime.now()
                
                # Emit signal
                self.data_sent.emit(connection_id, data)
                
                return True
                
        except Exception as e:
            self.logger.error(f"Error sending data: {e}")
            connection_info.error_count += 1
            
        return False
        
    async def receive_data(self, connection_id: str) -> Optional[bytes]:
        """Receive data from a connection"""
        try:
            if connection_id in self.connections:
                connection_info = self.connections[connection_id]
                
                # Receive data
                if connection_info.protocol in [NetworkProtocol.HTTP, NetworkProtocol.HTTPS]:
                    data = await self._receive_http(connection_info)
                elif connection_info.protocol in [NetworkProtocol.WS, NetworkProtocol.WSS]:
                    data = await self._receive_websocket(connection_info)
                elif connection_info.protocol in [NetworkProtocol.TCP, NetworkProtocol.UDP]:
                    data = await self._receive_socket(connection_info)
                    
                if data:
                    # Update stats
                    connection_info.bytes_received += len(data)
                    connection_info.last_activity = datetime.now()
                    
                    # Emit signal
                    self.data_received.emit(connection_id, data)
                    
                    return data
                    
        except Exception as e:
            self.logger.error(f"Error receiving data: {e}")
            connection_info.error_count += 1
            
        return None
        
    def _check_connections(self):
        """Check active connections"""
        try:
            for connection_id, connection_info in list(self.connections.items()):
                try:
                    # Check connection state
                    if connection_info.state == ConnectionState.CONNECTED:
                        # Check timeout
                        if (datetime.now() - connection_info.last_activity).total_seconds() > connection_info.timeout:
                            asyncio.create_task(self.disconnect(connection_id))
                            continue
                            
                        # Check keep-alive
                        if (datetime.now() - connection_info.last_activity).total_seconds() > self.keep_alive_interval:
                            asyncio.create_task(self._send_keep_alive(connection_info))
                            
                except Exception as e:
                    self.logger.error(f"Error checking connection {connection_id}: {e}")
                    connection_info.state = ConnectionState.ERROR
                    self.connection_error.emit(connection_id, str(e))
                    
        except Exception as e:
            self.logger.error(f"Error checking connections: {e}")
            
    def _cleanup_connections(self):
        """Clean up inactive connections"""
        try:
            for connection_id, connection_info in list(self.connections.items()):
                if connection_info.state in [ConnectionState.DISCONNECTED, ConnectionState.ERROR]:
                    del self.connections[connection_id]
                    
        except Exception as e:
            self.logger.error(f"Error cleaning up connections: {e}")
            
    def get_connection_info(self, connection_id: str) -> Optional[ConnectionInfo]:
        """Get connection information"""
        return self.connections.get(connection_id)
        
    def get_connection_list(self) -> List[ConnectionInfo]:
        """Get list of all connections"""
        return list(self.connections.values())
        
    def get_connection_history(self) -> List[ConnectionInfo]:
        """Get connection history"""
        return self.connection_history
        
    def set_connection_timeout(self, connection_id: str, timeout: float) -> bool:
        """Set connection timeout"""
        try:
            if connection_id in self.connections:
                self.connections[connection_id].timeout = timeout
                return True
                
        except Exception as e:
            self.logger.error(f"Error setting connection timeout: {e}")
            
        return False 