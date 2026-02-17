import { useEffect, useRef } from "react";
import { useChatStore } from "../stores/chatStore";
import { TranscriptMessage } from "./TranscriptMessage";

export function TranscriptPanel() {
  const messages = useChatStore((s) => s.messages);
  const bottomRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);
  const userScrolledUp = useRef(false);

  // Detect if user has scrolled up
  const handleScroll = () => {
    const el = containerRef.current;
    if (!el) return;
    const threshold = 100;
    userScrolledUp.current =
      el.scrollHeight - el.scrollTop - el.clientHeight > threshold;
  };

  // Auto-scroll to bottom on new messages (unless user scrolled up)
  useEffect(() => {
    if (!userScrolledUp.current) {
      bottomRef.current?.scrollIntoView({ behavior: "smooth" });
    }
  }, [messages]);

  return (
    <div className="transcript-panel" ref={containerRef} onScroll={handleScroll}>
      {messages.length === 0 ? (
        <div className="transcript-empty">
          <p>Start speaking or type a message to begin.</p>
          <p className="hint">The assistant can search the web and remembers your conversations.</p>
        </div>
      ) : (
        messages.map((entry) => (
          <TranscriptMessage key={entry.id} entry={entry} />
        ))
      )}
      <div ref={bottomRef} />
    </div>
  );
}
