# Voice Chat

A local voice chat application powered by a LangChain agent with real-time speech-to-text, text-to-speech, web search, and long-term memory.

Everything runs on your machine — your conversations never leave your MacBook.

## Features

- **Real-time voice conversation** — Speak naturally; the assistant responds with synthesized speech
- **Live transcript** — Full conversation history with speaker attribution and timestamps
- **Web search** — The assistant can search the web via Brave Search (says "Hold on, let me check that out" before searching)
- **Long-term memory** — Conversations are stored as markdown files by date and indexed with vector embeddings for semantic recall
- **Heartbeat system** — Configurable periodic prompts that make the assistant proactive (time awareness, memory reflection, proactive search, mood check)
- **Text fallback** — Type messages when voice isn't practical
- **Dark "nighttime radio" UI** — Minimal, calm interface with a pulsing orb visualization

## Architecture

```
Browser (React + VAD)  ←→  WebSocket  ←→  FastAPI Server
                                            ├── STT (Lightning Whisper MLX)
                                            ├── LangGraph Agent + Brave Search
                                            ├── TTS (Kokoro via mlx-audio)
                                            └── Memory (ChromaDB + Markdown)
```

## Prerequisites

- **macOS** with Apple Silicon (M1/M2/M3/M4) — required for MLX-based STT and TTS
- **Python 3.11+**
- **Node.js 18+**
- **Ollama** — for the local LLM ([install](https://ollama.ai))
- **Brave Search API key** — free tier at [brave.com/search/api](https://brave.com/search/api/)

## Setup

### 1. Install Ollama and pull a model

```bash
# Install Ollama (if not already installed)
brew install ollama

# Pull the default model
ollama pull llama3.1
```

### 2. Configure environment

```bash
cp .env.example .env
# Edit .env and set your BRAVE_SEARCH_API_KEY
```

### 3. Install backend dependencies

```bash
cd backend
pip install -e .
```

### 4. Install frontend dependencies

```bash
cd frontend
npm install
```

### 5. Start the backend

```bash
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000
```

The first request will download STT (~1.5GB) and TTS (~170MB) models automatically.

### 6. Start the frontend

```bash
cd frontend
npm run dev
```

### 7. Open the app

Navigate to [http://localhost:5173](http://localhost:5173) and start speaking.

## Configuration

All settings are in `.env`:

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | LLM API endpoint (Ollama) |
| `LLM_API_KEY` | `ollama` | API key for the LLM |
| `LLM_MODEL` | `llama3.1` | Model name |
| `BRAVE_SEARCH_API_KEY` | — | Your Brave Search API key |
| `STT_MODEL` | `distil-large-v3` | Whisper model variant |
| `TTS_MODEL` | `mlx-community/Kokoro-82M-bf16` | TTS model |
| `TTS_VOICE` | `af_heart` | Kokoro voice preset |
| `MEMORY_DIR` | `../memory` | Where memory files are stored |

### Using a different LLM

To use OpenAI instead of Ollama:
```
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o
```

Any OpenAI-compatible endpoint works (LM Studio, vLLM, etc).

## Memory System

Conversations are stored in two places:

1. **Markdown files** in `memory/conversations/YYYY-MM-DD.md` — human-readable, grep-able
2. **ChromaDB vectors** in `memory/.chromadb/` — for semantic search

The agent retrieves the top 3 most relevant past conversations before responding, plus today's conversation history.

## Heartbeat System

The assistant has periodic background "heartbeats" that make it proactive:

| Heartbeat | Default Interval | Purpose |
|-----------|-----------------|---------|
| Time Awareness | 30 min | Check in if the user has been quiet |
| Memory Reflection | 60 min | Surface unresolved threads or action items |
| Proactive Search | 120 min | Find relevant news or updates |
| Mood/Energy Check | 45 min | Natural check-in on the user |

Configure heartbeats via the gear icon in the UI, or edit `memory/heartbeats.json` directly.

## Project Structure

```
voice-chat/
├── backend/
│   ├── main.py            # FastAPI app + WebSocket endpoint
│   ├── ws_handler.py      # STT → Agent → TTS pipeline
│   ├── agent.py           # LangGraph agent definition
│   ├── tools.py           # Brave Search tool
│   ├── stt.py             # Lightning Whisper MLX wrapper
│   ├── tts.py             # Kokoro TTS wrapper
│   ├── memory.py          # ChromaDB + markdown memory
│   ├── heartbeat.py       # Proactive heartbeat scheduler
│   ├── protocol.py        # WebSocket message types
│   └── config.py          # Settings from .env
├── frontend/
│   └── src/
│       ├── App.tsx         # Root component with VAD
│       ├── hooks/          # useVoiceChat, useWebSocket, useAudioPlayback
│       ├── components/     # VoicePanel, VoiceOrb, TranscriptPanel, etc.
│       └── stores/         # Zustand state management
└── memory/                 # Conversation logs + ChromaDB (created at runtime)
```

## Estimated Resource Usage

On M4 Max with 64GB unified memory:

| Component | Memory | Notes |
|-----------|--------|-------|
| Whisper distil-large-v3 | ~1.5 GB | STT model |
| Kokoro 82M | ~170 MB | TTS model |
| Ollama llama3.1 (8B) | ~5 GB | LLM |
| ChromaDB + embeddings | ~200 MB | Memory system |
| **Total** | **~7 GB** | Leaves ~57 GB free |
