import { create } from "zustand";
import type { AppState, TranscriptEntry } from "../types";

interface ChatStore {
  messages: TranscriptEntry[];
  appState: AppState;
  isConnected: boolean;

  addUserMessage: (id: string, text: string) => void;
  startAssistantMessage: (id: string, isHeartbeat?: boolean) => void;
  appendAssistantText: (id: string, delta: string) => void;
  finalizeAssistantMessage: (id: string, fullText: string) => void;
  addToolUse: (
    id: string,
    toolName: string,
    query: string,
    summary?: string
  ) => void;
  updateToolResult: (id: string, toolName: string, summary: string) => void;
  setAppState: (state: AppState) => void;
  setConnected: (connected: boolean) => void;
}

export const useChatStore = create<ChatStore>((set) => ({
  messages: [],
  appState: "idle",
  isConnected: false,

  addUserMessage: (id, text) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id,
          role: "user",
          text,
          timestamp: Date.now(),
          toolUses: [],
          isStreaming: false,
          isHeartbeat: false,
        },
      ],
    })),

  startAssistantMessage: (id, isHeartbeat = false) =>
    set((state) => ({
      messages: [
        ...state.messages,
        {
          id,
          role: "assistant",
          text: "",
          timestamp: Date.now(),
          toolUses: [],
          isStreaming: true,
          isHeartbeat,
        },
      ],
    })),

  appendAssistantText: (id, delta) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id
          ? { ...m, text: m.text + (m.text ? " " : "") + delta }
          : m
      ),
    })),

  finalizeAssistantMessage: (id, fullText) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id ? { ...m, text: fullText, isStreaming: false } : m
      ),
    })),

  addToolUse: (id, toolName, query, summary) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id
          ? {
              ...m,
              toolUses: [...m.toolUses, { toolName, query, summary }],
            }
          : m
      ),
    })),

  updateToolResult: (id, toolName, summary) =>
    set((state) => ({
      messages: state.messages.map((m) =>
        m.id === id
          ? {
              ...m,
              toolUses: m.toolUses.map((t) =>
                t.toolName === toolName && !t.summary
                  ? { ...t, summary }
                  : t
              ),
            }
          : m
      ),
    })),

  setAppState: (appState) => set({ appState }),
  setConnected: (isConnected) => set({ isConnected }),
}));
