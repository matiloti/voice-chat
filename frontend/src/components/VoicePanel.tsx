import { useState } from "react";
import { useChatStore } from "../stores/chatStore";
import { VoiceOrb } from "./VoiceOrb";
import { StatusIndicator } from "./StatusIndicator";
import { HeartbeatSettings } from "./HeartbeatSettings";

interface VoicePanelProps {
  micEnabled: boolean;
  onToggleMic: (enabled: boolean) => void;
  onSendText: (text: string) => void;
}

export function VoicePanel({ micEnabled, onToggleMic, onSendText }: VoicePanelProps) {
  const { appState, isConnected } = useChatStore();
  const [showSettings, setShowSettings] = useState(false);
  const [textInput, setTextInput] = useState("");

  const handleTextSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (textInput.trim()) {
      onSendText(textInput);
      setTextInput("");
    }
  };

  return (
    <div className="voice-panel">
      <div className="voice-panel-header">
        <h1 className="app-title">Voice Chat</h1>
        <button
          className="settings-btn"
          onClick={() => setShowSettings(!showSettings)}
          title="Heartbeat Settings"
        >
          {showSettings ? "×" : "⚙"}
        </button>
      </div>

      {showSettings ? (
        <HeartbeatSettings onClose={() => setShowSettings(false)} />
      ) : (
        <>
          <div className="orb-container">
            <VoiceOrb appState={appState} />
          </div>

          <StatusIndicator isConnected={isConnected} appState={appState} />

          <div className="controls">
            <button
              className={`mic-btn ${micEnabled ? "active" : ""}`}
              onClick={() => onToggleMic(!micEnabled)}
              disabled={!isConnected}
            >
              {micEnabled ? "🎙 Mic On" : "🔇 Mic Off"}
            </button>
          </div>

          <form className="text-input-form" onSubmit={handleTextSubmit}>
            <input
              type="text"
              value={textInput}
              onChange={(e) => setTextInput(e.target.value)}
              placeholder="Type a message..."
              disabled={!isConnected}
            />
            <button type="submit" disabled={!isConnected || !textInput.trim()}>
              Send
            </button>
          </form>
        </>
      )}
    </div>
  );
}
