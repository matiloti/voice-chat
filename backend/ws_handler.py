"""WebSocket connection handler — orchestrates STT → Agent → TTS pipeline."""

import asyncio
import base64
import json
import logging
import re
from datetime import datetime

from fastapi import WebSocket, WebSocketDisconnect
from langchain_core.messages import HumanMessage

from protocol import (
    serialize, new_message_id,
    TranscriptFinal, AgentTextDelta, AgentTextDone,
    AgentAudioChunk, AgentAudioDone,
    ToolStart, ToolResult, HeartbeatStart, ErrorMsg, Pong,
)
from stt import STTEngine
from tts import TTSEngine
from memory import MemoryManager
from agent import create_agent, SYSTEM_PROMPT, HEARTBEAT_ADDENDUM

logger = logging.getLogger(__name__)

# Shared lazy-loaded singletons
_stt: STTEngine | None = None
_tts: TTSEngine | None = None
_memory: MemoryManager | None = None
_agent = None


def _get_stt() -> STTEngine:
    global _stt
    if _stt is None:
        _stt = STTEngine()
    return _stt


def _get_tts() -> TTSEngine:
    global _tts
    if _tts is None:
        _tts = TTSEngine()
    return _tts


def _get_memory() -> MemoryManager:
    global _memory
    if _memory is None:
        _memory = MemoryManager()
    return _memory


def _get_agent():
    global _agent
    if _agent is None:
        _agent = create_agent()
    return _agent


# Sentence boundary regex — splits on .!? followed by space or end of string
SENTENCE_BOUNDARY = re.compile(r'(?<=[.!?])\s+|(?<=[.!?])$')


def split_into_sentences(text: str) -> list[str]:
    """Split text into sentences at natural boundaries."""
    sentences = SENTENCE_BOUNDARY.split(text)
    return [s.strip() for s in sentences if s.strip()]


async def process_agent_response(
    ws: WebSocket,
    user_text: str,
    message_id: str,
    is_heartbeat: bool = False,
    heartbeat_name: str = "",
    heartbeat_prompt: str = "",
) -> None:
    """Run the agent and stream text + audio back to the client."""
    tts = _get_tts()
    memory = _get_memory()
    agent = _get_agent()

    # Retrieve memory context
    memory_context_parts = []
    past_memories = await memory.retrieve(user_text)
    if past_memories:
        memory_context_parts.append(f"## Relevant memories from past conversations:\n{past_memories}")
    today_context = await memory.get_today_context()
    if today_context:
        memory_context_parts.append(f"## Earlier today:\n{today_context}")
    memory_context = "\n\n".join(memory_context_parts) if memory_context_parts else "No memories from past conversations yet."

    # Build agent input
    if is_heartbeat:
        # For heartbeats, inject the heartbeat instruction into the user message
        heartbeat_msg = HEARTBEAT_ADDENDUM.format(
            heartbeat_name=heartbeat_name,
            heartbeat_prompt=heartbeat_prompt,
        )
        messages = [HumanMessage(content=heartbeat_msg)]
    else:
        messages = [HumanMessage(content=user_text)]

    initial_state = {
        "messages": messages,
        "memory_context": memory_context,
        "current_date": datetime.now().strftime("%Y-%m-%d"),
    }

    # Stream the agent response
    full_text = ""
    sentence_buffer = ""
    segment_index = 0
    tool_annotations = []

    try:
        async for event in agent.astream_events(initial_state, version="v2"):
            event_type = event.get("event", "")

            if event_type == "on_chat_model_stream":
                chunk = event.get("data", {}).get("chunk")
                if chunk and hasattr(chunk, "content") and chunk.content:
                    raw = chunk.content
                    # content may be a list of blocks (e.g. reasoning models)
                    if isinstance(raw, list):
                        token = "".join(
                            b.get("text", "") if isinstance(b, dict) else str(b)
                            for b in raw
                        )
                    else:
                        token = raw
                    if not token:
                        continue
                    sentence_buffer += token
                    full_text += token

                    # Check for sentence boundary
                    if re.search(r'[.!?]\s*$', sentence_buffer):
                        sentence = sentence_buffer.strip()
                        sentence_buffer = ""

                        if sentence:
                            # Check for heartbeat silence
                            if is_heartbeat and "[SILENT]" in sentence:
                                return  # Agent chose silence

                            # Send text delta
                            await ws.send_text(serialize(AgentTextDelta(
                                delta=sentence,
                                message_id=message_id,
                            )))

                            # Generate and send TTS audio
                            audio_bytes = await tts.synthesize(sentence)
                            if audio_bytes:
                                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
                                await ws.send_text(serialize(AgentAudioChunk(
                                    audio=audio_b64,
                                    message_id=message_id,
                                    segment_index=segment_index,
                                )))
                                segment_index += 1

            elif event_type == "on_tool_start":
                tool_name = event.get("name", "unknown")
                tool_input = str(event.get("data", {}).get("input", ""))
                tool_annotations.append(f'[Searched: "{tool_input}"]')
                await ws.send_text(serialize(ToolStart(
                    tool_name=tool_name,
                    tool_input=tool_input,
                    message_id=message_id,
                )))

            elif event_type == "on_tool_end":
                tool_name = event.get("name", "unknown")
                output = str(event.get("data", {}).get("output", ""))
                await ws.send_text(serialize(ToolResult(
                    tool_name=tool_name,
                    result_summary=output[:300],
                    message_id=message_id,
                )))

        # Flush remaining buffer
        if sentence_buffer.strip():
            sentence = sentence_buffer.strip()

            if is_heartbeat and "[SILENT]" in sentence:
                return

            await ws.send_text(serialize(AgentTextDelta(
                delta=sentence,
                message_id=message_id,
            )))
            full_text_final = full_text.strip()

            audio_bytes = await tts.synthesize(sentence)
            if audio_bytes:
                audio_b64 = base64.b64encode(audio_bytes).decode("ascii")
                await ws.send_text(serialize(AgentAudioChunk(
                    audio=audio_b64,
                    message_id=message_id,
                    segment_index=segment_index,
                )))

        # Check if entire response is silent (heartbeat)
        if is_heartbeat and "[SILENT]" in full_text:
            return

        # Send completion messages
        await ws.send_text(serialize(AgentTextDone(
            full_text=full_text.strip(),
            message_id=message_id,
        )))
        await ws.send_text(serialize(AgentAudioDone(
            message_id=message_id,
        )))

        # Store in memory (skip heartbeat-only interactions)
        if not is_heartbeat and user_text and full_text.strip():
            annotation_str = " ".join(tool_annotations)
            await memory.store(user_text, full_text.strip(), annotation_str)

    except Exception as e:
        logger.error("Agent processing error: %s", e, exc_info=True)
        await ws.send_text(serialize(ErrorMsg(detail=str(e))))


async def handle_connection(ws: WebSocket) -> None:
    """Main WebSocket connection handler."""
    await ws.accept()
    logger.info("WebSocket connection established.")

    # Send ready signal
    await ws.send_text(serialize(Pong()))

    # Import heartbeat scheduler
    from heartbeat import HeartbeatScheduler
    scheduler = HeartbeatScheduler(ws)
    await scheduler.start()

    try:
        while True:
            raw = await ws.receive_text()
            try:
                msg = json.loads(raw)
            except json.JSONDecodeError:
                await ws.send_text(serialize(ErrorMsg(detail="Invalid JSON")))
                continue

            msg_type = msg.get("type", "")

            if msg_type == "ping":
                await ws.send_text(serialize(Pong()))

            elif msg_type == "audio_chunk":
                message_id = new_message_id()
                audio_b64 = msg.get("audio", "")

                try:
                    wav_bytes = base64.b64decode(audio_b64)
                except Exception:
                    await ws.send_text(serialize(ErrorMsg(detail="Invalid base64 audio")))
                    continue

                # Pause heartbeats during active processing
                scheduler.pause()

                # Transcribe
                stt = _get_stt()
                try:
                    transcript = await stt.transcribe(wav_bytes)
                except Exception as e:
                    logger.error("STT failed: %s", e)
                    await ws.send_text(serialize(ErrorMsg(detail=f"Transcription failed: {e}")))
                    scheduler.resume()
                    continue

                if not transcript:
                    scheduler.resume()
                    continue

                # Send transcript to client
                await ws.send_text(serialize(TranscriptFinal(
                    text=transcript,
                    message_id=message_id,
                )))

                # Process with agent (separate ID for assistant response)
                assistant_id = new_message_id()
                await process_agent_response(ws, transcript, assistant_id)
                scheduler.resume()

            elif msg_type == "text_input":
                message_id = new_message_id()
                text = msg.get("text", "").strip()

                if not text:
                    continue

                scheduler.pause()

                # Send as transcript
                await ws.send_text(serialize(TranscriptFinal(
                    text=text,
                    message_id=message_id,
                )))

                # Process with agent (separate ID for assistant response)
                assistant_id = new_message_id()
                await process_agent_response(ws, text, assistant_id)
                scheduler.resume()

            else:
                logger.warning("Unknown message type: %s", msg_type)

    except WebSocketDisconnect:
        logger.info("WebSocket disconnected.")
    except Exception as e:
        logger.error("WebSocket error: %s", e, exc_info=True)
    finally:
        await scheduler.stop()
