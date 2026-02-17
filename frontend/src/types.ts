/** WebSocket message types shared between client and server. */

// ---- App State ----

export type AppState =
  | "idle"
  | "listening"
  | "processing"
  | "thinking"
  | "speaking";

// ---- Client -> Server ----

export interface AudioChunkMessage {
  type: "audio_chunk";
  audio: string; // base64-encoded WAV (16kHz, mono, 16-bit PCM)
  timestamp: number;
}

export interface TextInputMessage {
  type: "text_input";
  text: string;
}

export interface PingMessage {
  type: "ping";
}

export type ClientMessage = AudioChunkMessage | TextInputMessage | PingMessage;

// ---- Server -> Client ----

export interface TranscriptFinalMessage {
  type: "transcript_final";
  text: string;
  message_id: string;
}

export interface AgentTextDeltaMessage {
  type: "agent_text_delta";
  delta: string;
  message_id: string;
}

export interface AgentTextDoneMessage {
  type: "agent_text_done";
  full_text: string;
  message_id: string;
}

export interface AgentAudioChunkMessage {
  type: "agent_audio_chunk";
  audio: string; // base64-encoded PCM float32, 24kHz mono
  message_id: string;
  segment_index: number;
}

export interface AgentAudioDoneMessage {
  type: "agent_audio_done";
  message_id: string;
}

export interface ToolStartMessage {
  type: "tool_start";
  tool_name: string;
  tool_input: string;
  message_id: string;
}

export interface ToolResultMessage {
  type: "tool_result";
  tool_name: string;
  result_summary: string;
  message_id: string;
}

export interface HeartbeatStartMessage {
  type: "heartbeat_start";
  heartbeat_name: string;
  message_id: string;
}

export interface ErrorMessage {
  type: "error";
  detail: string;
}

export interface PongMessage {
  type: "pong";
}

export type ServerMessage =
  | TranscriptFinalMessage
  | AgentTextDeltaMessage
  | AgentTextDoneMessage
  | AgentAudioChunkMessage
  | AgentAudioDoneMessage
  | ToolStartMessage
  | ToolResultMessage
  | HeartbeatStartMessage
  | ErrorMessage
  | PongMessage;

// ---- Transcript Entry (UI state) ----

export interface ToolUse {
  toolName: string;
  query: string;
  summary?: string;
}

export interface TranscriptEntry {
  id: string;
  role: "user" | "assistant";
  text: string;
  timestamp: number;
  toolUses: ToolUse[];
  isStreaming: boolean;
  isHeartbeat: boolean;
}

// ---- Heartbeat Config ----

export interface HeartbeatConfig {
  id: string;
  name: string;
  prompt: string;
  interval_minutes: number;
  enabled: boolean;
}
