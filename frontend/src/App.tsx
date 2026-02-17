import { useMicVAD } from "@ricky0123/vad-react";
import { useVoiceChat } from "./hooks/useVoiceChat";
import { VoicePanel } from "./components/VoicePanel";
import { TranscriptPanel } from "./components/TranscriptPanel";
import { useChatStore } from "./stores/chatStore";

export default function App() {
  const {
    onSpeechEnd,
    onSpeechStart,
    sendTextMessage,
    micEnabled,
    setMicEnabled,
  } = useVoiceChat();
  const isConnected = useChatStore((s) => s.isConnected);

  // Initialize VAD — only processes audio when mic is enabled and connected
  useMicVAD({
    startOnLoad: true,
    onSpeechStart: () => {
      if (micEnabled && isConnected) {
        onSpeechStart();
      }
    },
    onSpeechEnd: (audio) => {
      if (micEnabled && isConnected) {
        onSpeechEnd(audio);
      }
    },
    workletURL: "/vad/vad.worklet.bundle.min.js",
    modelURL: "/vad/silero_vad_legacy.onnx",
    ortConfig: (ort) => {
      ort.env.wasm.wasmPaths = "/vad/";
    },
  });

  return (
    <div className="app">
      <VoicePanel
        micEnabled={micEnabled}
        onToggleMic={setMicEnabled}
        onSendText={sendTextMessage}
      />
      <TranscriptPanel />
    </div>
  );
}
