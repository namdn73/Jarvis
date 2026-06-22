import asyncio
from dataclasses import dataclass, field
from enum import Enum


class JarvisStatus(str, Enum):
    STANDBY       = "STANDBY"
    GREETING      = "GREETING"
    LISTENING     = "LISTENING"
    PROCESSING    = "PROCESSING"
    RESPONDING    = "RESPONDING"
    ACTIVE_WINDOW = "ACTIVE_WINDOW"


@dataclass
class JarvisState:
    status:      JarvisStatus       = JarvisStatus.STANDBY
    transcript:  str                = ""
    results:     list[dict]         = field(default_factory=list)
    preferences: dict               = field(default_factory=dict)


# Shared queue — audio thread writes via loop.call_soon_threadsafe(message_queue.put_nowait, msg)
message_queue: asyncio.Queue = asyncio.Queue()

# Singleton state instance used across the process
state = JarvisState()
