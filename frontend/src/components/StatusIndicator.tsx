import type { AppState } from "../types";

interface StatusIndicatorProps {
  isConnected: boolean;
  appState: AppState;
}

const STATE_LABELS: Record<AppState, string> = {
  idle: "Ready",
  listening: "Listening...",
  processing: "Processing...",
  thinking: "Thinking...",
  speaking: "Speaking...",
};

export function StatusIndicator({ isConnected, appState }: StatusIndicatorProps) {
  return (
    <div className="status-indicator">
      <span
        className={`status-dot ${isConnected ? "connected" : "disconnected"}`}
      />
      <span className="status-text">
        {isConnected ? STATE_LABELS[appState] : "Disconnected"}
      </span>
    </div>
  );
}
