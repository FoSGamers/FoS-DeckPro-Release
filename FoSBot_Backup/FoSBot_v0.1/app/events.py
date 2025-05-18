from dataclasses import dataclass, field; from typing import Optional, Dict, Any, List; import datetime # List added
@dataclass
class InternalChatMessage: platform: str; user: str; text: str; channel: Optional[str]=None; user_id: Optional[str]=None; display_name: Optional[str]=None; timestamp: datetime.datetime=field(default_factory=datetime.datetime.utcnow); message_id: Optional[str]=None; is_command: bool=False; raw_data: Dict[str,Any]=field(default_factory=dict)
@dataclass
class BotResponse: target_platform: str; text: str; target_channel: Optional[str]=None; reply_to_user: Optional[str]=None; reply_to_message_id: Optional[str]=None
class Event: pass
@dataclass
class ChatMessageReceived(Event): message: InternalChatMessage
@dataclass
class CommandDetected(Event): command: str; args: list[str]; source_message: InternalChatMessage
@dataclass
class BotResponseToSend(Event): response: BotResponse
@dataclass
class StreamerInputReceived(Event): text: str
@dataclass
class BroadcastStreamerMessage(Event): text: str
@dataclass
class PlatformStatusUpdate(Event): platform: str; status: str; message: Optional[str]=None
@dataclass
class LogMessage(Event): level: str; message: str; module: Optional[str]=None
@dataclass
class SettingsUpdated(Event): keys_updated: List[str] # List of keys changed
@dataclass
class ServiceControl(Event): service_name: str; command: str # 'start', 'stop', 'restart'
@dataclass
class GameEvent(Event): pass # Base for game events
