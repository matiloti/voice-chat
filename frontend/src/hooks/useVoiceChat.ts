import { useCallback, useRef, useState } from "react";
import { useChatStore } from "../stores/chatStore";
import { useWebSocket } from "./useWebSocket";
import { useAudioPlayback } from "./useAudioPlayback";
import type { ServerMessage } from "../types";

/**
 * Encode Float32Array (from VAD) to a base64-encoded WAV string.
 * VAD delivers 16kHz mono float32 audio.
 */
function encodeWav(samples: Float32Array, sampleRate: number): string {
  const numChannels = 1;
  const bitsPerSample = 16;
  const byteRate = sampleRate * numChannels * (bitsPerSample / 8);
  const blockAlign = numChannels * (bitsPerSample / 8);

  // Convert float32 to int16
  const pcm16 = new Int16Array(samples.length);
  for (let i = 0; i < samples.length; i++) {
    const s = Math.max(-1, Math.min(1, samples[i]));
    pcm16[i] = s < 0 ? s * 0x8000 : s * 0x7fff;
  }

  const dataLength = pcm16.length * 2;
  const buffer = new ArrayBuffer(44 + dataLength);
  const view = new DataView(buffer);

  // WAV header
  writeString(view, 0, "RIFF");
  view.setUint32(4, 36 + dataLength, true);
  writeString(view, 8, "WAVE");
  writeString(view, 12, "fmt ");
  view.setUint32(16, 16, true); // chunk size
  view.setUint16(20, 1, true); // PCM
  view.setUint16(22, numChannels, true);
  view.setUint32(24, sampleRate, true);
  view.setUint32(28, byteRate, true);
  view.setUint16(32, blockAlign, true);
  view.setUint16(34, bitsPerSample, true);
  writeString(view, 36, "data");
  view.setUint32(40, dataLength, true);

  // PCM data
  const pcmBytes = new Uint8Array(buffer, 44);
  pcmBytes.set(new Uint8Array(pcm16.buffer));

  // Base64 encode
  let binary = "";
  const bytes = new Uint8Array(buffer);
  for (let i = 0; i < bytes.length; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}

function writeString(view: DataView, offset: number, str: string) {
  for (let i = 0; i < str.length; i++) {
    view.setUint8(offset + i, str.charCodeAt(i));
  }
}

export function useVoiceChat() {
  const store = useChatStore();
  const { enqueueAudio, stopPlayback } = useAudioPlayback();
  const [micEnabled, setMicEnabled] = useState(true);
  const activeMessageRef = useRef<string | null>(null);

  const handleServerMessage = useCallback(
    (msg: ServerMessage) => {
      switch (msg.type) {
        case "pong":
          // Server ready or heartbeat response
          break;

        case "transcript_final":
          store.addUserMessage(msg.message_id, msg.text);
          store.setAppState("thinking");
          activeMessageRef.current = msg.message_id;
          break;

        case "agent_text_delta":
          // Create assistant message if not yet started
          if (activeMessageRef.current !== msg.message_id) {
            store.startAssistantMessage(msg.message_id);
            activeMessageRef.current = msg.message_id;
          }
          store.appendAssistantText(msg.message_id, msg.delta);
          break;

        case "agent_text_done":
          store.finalizeAssistantMessage(msg.message_id, msg.full_text);
          break;

        case "agent_audio_chunk":
          enqueueAudio(msg.audio);
          break;

        case "agent_audio_done":
          activeMessageRef.current = null;
          break;

        case "tool_start":
          if (activeMessageRef.current !== msg.message_id) {
            store.startAssistantMessage(msg.message_id);
            activeMessageRef.current = msg.message_id;
          }
          store.addToolUse(
            msg.message_id,
            msg.tool_name,
            msg.tool_input
          );
          break;

        case "tool_result":
          store.updateToolResult(
            msg.message_id,
            msg.tool_name,
            msg.result_summary
          );
          break;

        case "heartbeat_start":
          // Heartbeat processing — create a heartbeat-tagged message
          store.startAssistantMessage(msg.message_id, true);
          activeMessageRef.current = msg.message_id;
          break;

        case "error":
          console.error("Server error:", msg.detail);
          store.setAppState("idle");
          break;
      }
    },
    [store, enqueueAudio]
  );

  const { sendMessage } = useWebSocket(handleServerMessage);

  const onSpeechEnd = useCallback(
    (audio: Float32Array) => {
      if (!micEnabled) return;

      const wavBase64 = encodeWav(audio, 16000);
      store.setAppState("processing");

      sendMessage({
        type: "audio_chunk",
        audio: wavBase64,
        timestamp: Date.now(),
      });
    },
    [sendMessage, store, micEnabled]
  );

  const onSpeechStart = useCallback(() => {
    store.setAppState("listening");
    // Stop any ongoing TTS playback (barge-in)
    stopPlayback();
  }, [store, stopPlayback]);

  const sendTextMessage = useCallback(
    (text: string) => {
      if (!text.trim()) return;
      store.setAppState("thinking");
      sendMessage({ type: "text_input", text: text.trim() });
    },
    [sendMessage, store]
  );

  return {
    onSpeechEnd,
    onSpeechStart,
    sendTextMessage,
    micEnabled,
    setMicEnabled,
  };
}
