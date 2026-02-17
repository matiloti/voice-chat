import { useRef, useCallback } from "react";
import { useChatStore } from "../stores/chatStore";

const SAMPLE_RATE = 24000; // Kokoro TTS output rate

export function useAudioPlayback() {
  const audioCtxRef = useRef<AudioContext | null>(null);
  const nextPlayTime = useRef(0);
  const playingCount = useRef(0);
  const { setAppState } = useChatStore();

  const getAudioContext = useCallback(() => {
    if (!audioCtxRef.current || audioCtxRef.current.state === "closed") {
      audioCtxRef.current = new AudioContext({ sampleRate: SAMPLE_RATE });
    }
    if (audioCtxRef.current.state === "suspended") {
      audioCtxRef.current.resume();
    }
    return audioCtxRef.current;
  }, []);

  const enqueueAudio = useCallback(
    (base64Audio: string) => {
      const ctx = getAudioContext();

      // Decode base64 to Float32Array
      const binaryStr = atob(base64Audio);
      const bytes = new Uint8Array(binaryStr.length);
      for (let i = 0; i < binaryStr.length; i++) {
        bytes[i] = binaryStr.charCodeAt(i);
      }
      const float32 = new Float32Array(bytes.buffer);

      // Create AudioBuffer
      const audioBuffer = ctx.createBuffer(1, float32.length, SAMPLE_RATE);
      audioBuffer.getChannelData(0).set(float32);

      // Schedule for gapless playback
      const source = ctx.createBufferSource();
      source.buffer = audioBuffer;
      source.connect(ctx.destination);

      const now = ctx.currentTime;
      const startTime = Math.max(now, nextPlayTime.current);
      source.start(startTime);
      nextPlayTime.current = startTime + audioBuffer.duration;

      playingCount.current++;
      setAppState("speaking");

      source.onended = () => {
        playingCount.current--;
        if (playingCount.current <= 0) {
          playingCount.current = 0;
          setAppState("idle");
        }
      };
    },
    [getAudioContext, setAppState]
  );

  const stopPlayback = useCallback(() => {
    if (audioCtxRef.current && audioCtxRef.current.state !== "closed") {
      audioCtxRef.current.close();
      audioCtxRef.current = null;
    }
    nextPlayTime.current = 0;
    playingCount.current = 0;
    setAppState("idle");
  }, [setAppState]);

  return { enqueueAudio, stopPlayback, getAudioContext };
}
