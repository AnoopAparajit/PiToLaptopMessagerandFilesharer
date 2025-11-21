import json
import struct
from enum import Enum
from dataclasses import dataclass, asdict
from typing import Any, Dict, Optional

# Constants
UDP_PORT = 5000
TCP_PORT = 5001
BUFFER_SIZE = 4096
BROADCAST_IP = '<broadcast>'
DISCOVERY_INTERVAL = 2.0  # Seconds

class MessageType(str, Enum):
    DISCOVERY = "DISCOVERY"
    TEXT = "TEXT"
    FILE_OFFER = "FILE_OFFER"
    FILE_ACCEPT = "FILE_ACCEPT"
    FILE_REJECT = "FILE_REJECT"
    FILE_DATA = "FILE_DATA"
    FILE_END = "FILE_END"

@dataclass
class Message:
    type: MessageType
    sender_name: str
    sender_ip: str
    payload: Dict[str, Any] = None

    def to_json(self) -> str:
        data = asdict(self)
        # Convert Enum to string for JSON serialization
        data['type'] = self.type.value
        return json.dumps(data)

    @staticmethod
    def from_json(json_str: str) -> 'Message':
        data = json.loads(json_str)
        data['type'] = MessageType(data['type'])
        return Message(**data)

    def to_bytes(self) -> bytes:
        json_str = self.to_json()
        return json_str.encode('utf-8')

    @staticmethod
    def from_bytes(data: bytes) -> 'Message':
        return Message.from_json(data.decode('utf-8'))
