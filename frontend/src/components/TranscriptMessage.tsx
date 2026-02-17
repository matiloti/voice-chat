import type { TranscriptEntry } from "../types";

interface TranscriptMessageProps {
  entry: TranscriptEntry;
}

function formatTime(ts: number): string {
  const d = new Date(ts);
  return d.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
}

export function TranscriptMessage({ entry }: TranscriptMessageProps) {
  return (
    <div className={`transcript-message ${entry.role} ${entry.isHeartbeat ? "heartbeat" : ""}`}>
      <div className="message-header">
        <span className="message-role">
          {entry.isHeartbeat && <span className="heartbeat-icon" title="Proactive message">♥ </span>}
          {entry.role === "user" ? "You" : "Assistant"}
        </span>
        <span className="message-time">{formatTime(entry.timestamp)}</span>
      </div>

      <div className="message-text">
        {entry.text}
        {entry.isStreaming && <span className="typing-indicator">▍</span>}
      </div>

      {entry.toolUses.length > 0 && (
        <div className="tool-uses">
          {entry.toolUses.map((tool, i) => (
            <div key={i} className="tool-use-card">
              <div className="tool-use-header">
                🔍 Searched: &quot;{tool.query}&quot;
              </div>
              {tool.summary && (
                <div className="tool-use-summary">{tool.summary}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
