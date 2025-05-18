# Version History: 0.7.2 -> 0.7.3
from dataclasses import dataclass
from datetime import datetime

@dataclass
class InternalChatMessage:
    platform: str
    channel: str
    user: str
    text: str
    timestamp: str

@dataclass
class ChatMessageReceived:
    message: InternalChatMessage

@dataclass
class PlatformStatusUpdate:
    platform: str
    status: str
    message: str = ""

@dataclass
class ServiceControl:
    service_name: str
    command: str

@dataclass
class SettingsUpdated:
    keys_updated: list

