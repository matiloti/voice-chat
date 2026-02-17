"""WebSocket message protocol definitions."""

from dataclasses import dataclass, asdict, field
from typing import Literal
import json
import uuid


def new_message_id() -> str:
    return uuid.uuid4().hex[:12]


def serialize(msg: object) -> str:
    return json.dumps(asdict(msg))  # type: ignore[arg-type]


# ---- Server -> Client Messages ----


@dataclass
class TranscriptFinal:
    text: str
    message_id: str
    type: Literal["transcript_final"] = "transcript_final"


@dataclass
class AgentTextDelta:
    delta: str
    message_id: str
    type: Literal["agent_text_delta"] = "agent_text_delta"


@dataclass
class AgentTextDone:
    full_text: str
    message_id: str
    type: Literal["agent_text_done"] = "agent_text_done"


@dataclass
class AgentAudioChunk:
    audio: str  # base64-encoded PCM float32, 24kHz mono
    message_id: str
    segment_index: int = 0
    type: Literal["agent_audio_chunk"] = "agent_audio_chunk"


@dataclass
class AgentAudioDone:
    message_id: str
    type: Literal["agent_audio_done"] = "agent_audio_done"


@dataclass
class ToolStart:
    tool_name: str
    tool_input: str
    message_id: str
    type: Literal["tool_start"] = "tool_start"


@dataclass
class ToolResult:
    tool_name: str
    result_summary: str
    message_id: str
    type: Literal["tool_result"] = "tool_result"


@dataclass
class HeartbeatStart:
    heartbeat_name: str
    message_id: str
    type: Literal["heartbeat_start"] = "heartbeat_start"


@dataclass
class ErrorMsg:
    detail: str
    type: Literal["error"] = "error"


@dataclass
class Pong:
    type: Literal["pong"] = "pong"
