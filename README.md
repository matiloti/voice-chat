# Voice Chat

A fully local voice chat application powered by a LangChain agent with real-time speech-to-text, text-to-speech, web search, long-term memory, and a proactive heartbeat system.

Everything runs on your machine. Your conversations stay private.

```
┌──────────────────┐              ┌──────────────────────────────────┐
│   Browser (React) │   WebSocket  │     Python Backend (FastAPI)      │
│                    │◄────────────►│                                    │
│  Microphone → VAD  │              │  STT: Lightning Whisper MLX       │
│  Pulsing Orb UI    │              │  Agent: LangGraph + Brave Search  │
│  Live Transcript   │              │  TTS: Kokoro via mlx-audio        │
│  Audio Playback    │              │  Memory: ChromaDB + Markdown      │
└──────────────────┘              │  Heartbeats: Proactive prompts    │
                                   └──────────────────────────────────┘
```

---

## Table of Contents

- [Features](#features)
- [System Requirements](#system-requirements)
- [Quick Start](#quick-start)
- [Detailed Setup Guide](#detailed-setup-guide)
  - [1. Install System Dependencies](#1-install-system-dependencies)
  - [2. Set Up Ollama (Local LLM)](#2-set-up-ollama-local-llm)
  - [3. Get a Brave Search API Key](#3-get-a-brave-search-api-key)
  - [4. Configure Environment Variables](#4-configure-environment-variables)
  - [5. Install and Run (Automated)](#5-install-and-run-automated)
  - [5b. Install and Run (Manual)](#5b-install-and-run-manual)
  - [6. Open and Use](#6-open-and-use)
- [How It Works](#how-it-works)
  - [Voice Pipeline](#voice-pipeline)
  - [WebSocket Protocol](#websocket-protocol)
  - [Agent Architecture](#agent-architecture)
  - [Memory System](#memory-system)
  - [Heartbeat System](#heartbeat-system)
- [Configuration Reference](#configuration-reference)
  - [Environment Variables](#environment-variables)
  - [LLM Provider Options](#llm-provider-options)
  - [STT Model Options](#stt-model-options)
  - [TTS Voice Options](#tts-voice-options)
- [Using the Application](#using-the-application)
  - [Voice Mode](#voice-mode)
  - [Text Fallback](#text-fallback)
  - [Barge-In (Interruption)](#barge-in-interruption)
  - [Configuring Heartbeats](#configuring-heartbeats)
  - [Reading Your Memory Files](#reading-your-memory-files)
- [Project Structure](#project-structure)
- [Resource Usage](#resource-usage)
- [Troubleshooting](#troubleshooting)
- [Development](#development)

---

## Features

- **Real-time voice conversation** — Speak naturally; the assistant hears you via browser-side Voice Activity Detection (Silero VAD), transcribes with Whisper, thinks with an LLM, and responds with synthesized speech
- **Sentence-level streaming** — Audio starts playing as soon as the first sentence is ready, not after the full response
- **Live transcript** — Full conversation history with speaker labels, timestamps, and tool-use cards
- **Web search** — The assistant can search the web via Brave Search and always announces it: *"Hold on, let me check that out"*
- **Long-term memory** — Every conversation is stored as a human-readable markdown file (organized by date) and indexed with vector embeddings for semantic recall across sessions
- **Heartbeat system** — Configurable periodic prompts that make the assistant proactive: it can check in on you, surface forgotten tasks, search for relevant news, or check your energy level
- **Barge-in support** — Start speaking while the assistant is talking; playback stops immediately and your new input takes priority
- **Text fallback** — Type messages when voice isn't practical
- **Dark UI** — Calm "nighttime radio" aesthetic with a pulsing orb that reacts to conversation state (blue = listening, amber = speaking, breathing = idle)

---

## System Requirements

| Requirement | Minimum | Recommended |
|-------------|---------|-------------|
| **macOS** | Apple Silicon (M1) | M4 Max |
| **Unified Memory** | 16 GB | 64 GB |
| **Python** | 3.11 | 3.12+ |
| **Node.js** | 18 | 20+ |
| **Disk** | 5 GB free (for models) | 10 GB |
| **Browser** | Chrome/Edge/Safari | Chrome (best Web Audio support) |

> **Apple Silicon is required.** The STT (Lightning Whisper MLX) and TTS (Kokoro via mlx-audio) engines use the [MLX framework](https://github.com/ml-explore/mlx) which is Apple Silicon only. This app will not run on Intel Macs or Linux/Windows.

---

## Quick Start

If you're experienced and just want to get running:

```bash
# 1. Prerequisites
brew install ollama node python@3.12
ollama serve &
ollama pull llama3.1

# 2. Configure
cp .env.example .env
# Edit .env → set BRAVE_SEARCH_API_KEY (get free key at https://brave.com/search/api/)

# 3. Run everything (creates venv, installs deps, starts both servers)
./run.sh

# 4. Open http://localhost:5173 and start talking
```

`run.sh` handles everything automatically: checks prerequisites, creates the Python virtual environment at `backend/.venv`, installs Python and npm dependencies, starts the backend (port 8000) and frontend (port 5173). On subsequent runs it skips installation and starts instantly.

You can also run components individually:
```bash
./run.sh backend   # Backend only (venv + uvicorn)
./run.sh frontend  # Frontend only (npm)
```

---

## Detailed Setup Guide

### 1. Install System Dependencies

**Homebrew** (if not installed):
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

**Python 3.11+:**
```bash
# Check current version
python3 --version

# Install if needed
brew install python@3.12
```

**Node.js 18+:**
```bash
# Check current version
node --version

# Install if needed
brew install node
```

**Xcode Command Line Tools** (required for native compilation of some Python packages):
```bash
xcode-select --install
```

### 2. Set Up Ollama (Local LLM)

[Ollama](https://ollama.ai) runs large language models locally. It serves an OpenAI-compatible API on `localhost:11434`.

**Install:**
```bash
brew install ollama
```

**Start the Ollama service:**
```bash
# Start in the background (stays running)
ollama serve
```

> Ollama also installs as a macOS app. If you prefer, download it from [ollama.ai](https://ollama.ai) and launch it — the menu bar icon means the service is running.

**Pull a model:**
```bash
# Default: Llama 3.1 8B (4.7 GB download)
ollama pull llama3.1

# Alternative: smaller/faster
ollama pull llama3.2          # 3B, 2 GB — faster, less capable
ollama pull mistral            # 7B, 4 GB — good general purpose

# Alternative: larger/smarter (needs 32GB+ RAM)
ollama pull llama3.1:70b      # 70B, 40 GB — much smarter, slow on <64GB
```

**Verify it works:**
```bash
ollama run llama3.1 "Say hello in one sentence"
# Should print a greeting and exit
```

> **Tip:** Ollama must be running whenever you use Voice Chat. If you see "Connection refused" errors, run `ollama serve` first.

### 3. Get a Brave Search API Key

The assistant uses [Brave Search](https://brave.com/search/api/) to look up real-time information. The free tier gives you 2,000 queries/month.

1. Go to [https://brave.com/search/api/](https://brave.com/search/api/)
2. Click **"Get started for free"**
3. Create an account or sign in
4. In the dashboard, go to **API Keys**
5. Create a new key — copy it

> **Optional:** If you don't set a Brave Search key, the app still works — the assistant just can't search the web. It'll tell you: *"Brave Search API key not configured."*

### 4. Configure Environment Variables

From the project root:

```bash
cp .env.example .env
```

Edit `.env` with your editor:

```bash
# .env

# LLM Configuration (Ollama by default)
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.1

# Brave Search API Key
BRAVE_SEARCH_API_KEY=BSA-xxxxxxxxxxxxxxxxxxxxxxxx

# STT Configuration
STT_MODEL=distil-large-v3

# TTS Configuration
TTS_MODEL=mlx-community/Kokoro-82M-bf16
TTS_VOICE=af_heart

# Memory directory
MEMORY_DIR=../memory
```

The only thing you **must** change is `BRAVE_SEARCH_API_KEY`. Everything else has sensible defaults.

### 5. Install and Run (Automated)

The easiest way — `run.sh` handles venv creation, dependency installation, and starting both servers:

```bash
# From the project root
./run.sh
```

This will:
1. Check that Python 3.11+ and Node.js 18+ are installed
2. Create a virtual environment at `backend/.venv` (if it doesn't exist)
3. Install all Python dependencies into the venv (if not already installed)
4. Install npm dependencies (if `node_modules/` doesn't exist)
5. Start the backend on port 8000 (background)
6. Start the frontend on port 5173 (foreground)

On subsequent runs, it skips all installation steps and starts immediately.

> **On first voice interaction**, you'll see STT and TTS model downloads in the backend logs:
> ```
> Loading STT model: distil-large-v3 (this may take a moment on first run)...
> STT model loaded.
> Loading TTS model: mlx-community/Kokoro-82M-bf16 ...
> TTS model loaded.
> ```
> The STT model (~1.5 GB) and TTS model (~170 MB) download once and are cached locally.

### 5b. Install and Run (Manual)

If you prefer to manage the venv yourself or run the servers in separate terminals:

**Backend:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Frontend (separate terminal):**
```bash
cd frontend
npm install
npm run dev
```

<details>
<summary>What gets installed</summary>

**Python packages (in `backend/.venv`):**
| Package | Purpose |
|---------|---------|
| `fastapi` + `uvicorn` | Web server + WebSocket |
| `lightning-whisper-mlx` | Speech-to-text (Whisper on Apple Silicon) |
| `mlx-audio` | Text-to-speech (Kokoro on Apple Silicon) |
| `langgraph` + `langchain` | Agent orchestration |
| `langchain-openai` | LLM integration (OpenAI-compatible API) |
| `langchain-community` | Brave Search tool |
| `chromadb` | Vector database for memory |
| `python-dotenv` | Environment variable loading |
| `numpy` | Audio array processing |

**npm packages (in `frontend/node_modules`):**
| Package | Purpose |
|---------|---------|
| `react` + `react-dom` | UI framework |
| `@ricky0123/vad-react` | Voice Activity Detection (Silero ONNX in browser) |
| `onnxruntime-web` | ONNX model runtime for VAD |
| `zustand` | State management |
| `vite` | Dev server + bundler |
| `vite-plugin-static-copy` | Copies VAD model files to public directory |

> **First install takes 2-5 minutes** due to native compilation of MLX packages.

**Verify the Python install:**
```bash
source backend/.venv/bin/activate
python3 -c "import fastapi, lightning_whisper_mlx, langgraph, chromadb; print('All packages OK')"
```

</details>

### 6. Open and Use

1. Open **http://localhost:5173** in Chrome (or any modern browser)
2. **Allow microphone access** when prompted
3. The pulsing orb should appear and the status should say **"Ready"**
4. **Start speaking** — the orb turns blue while you talk
5. When you stop, the orb turns yellow (processing), then amber (assistant speaking)
6. The transcript appears in the right panel

---

## How It Works

### Voice Pipeline

The end-to-end latency target is **~1-1.5 seconds** from when you stop speaking to when the assistant's voice starts playing:

```
You speak (browser)
    │
    ▼
VAD detects speech end (Silero, ~30ms)
    │
    ▼
Audio encoded as WAV → base64 → sent over WebSocket
    │
    ▼
STT transcribes (Lightning Whisper MLX, ~200ms for short utterances)
    │
    ▼
Transcript sent to client + fed to LangGraph agent
    │
    ▼
Agent streams tokens → buffered into complete sentences
    │
    ├─── Sentence 1 ready → TTS generates audio (~120ms) → sent to client → plays
    ├─── Sentence 2 ready → TTS generates audio → sent to client → queued behind sentence 1
    └─── ...
    │
    ▼
Agent done → memory stored (markdown + ChromaDB)
```

Key design choices:
- **Sentence-level streaming:** LLM tokens are buffered until a sentence boundary (`.` `!` `?`), then text and audio are sent simultaneously. This provides natural speech cadence.
- **Lazy model loading:** STT and TTS models only load when the first audio arrives, keeping server startup instant during development.
- **All inference in threads:** STT and TTS run in `asyncio.to_thread()` to avoid blocking the event loop.

### WebSocket Protocol

All messages are JSON text frames. Audio is base64-encoded.

**Client → Server:**

| Message Type | Payload | When Sent |
|-------------|---------|-----------|
| `audio_chunk` | `{ type, audio: "<base64 WAV>", timestamp }` | VAD detects end of speech |
| `text_input` | `{ type, text }` | User types and submits a message |
| `ping` | `{ type }` | Every 15 seconds (keepalive) |

**Server → Client:**

| Message Type | Payload | When Sent |
|-------------|---------|-----------|
| `transcript_final` | `{ type, text, message_id }` | STT transcription complete |
| `agent_text_delta` | `{ type, delta, message_id }` | Each sentence of agent's response |
| `agent_text_done` | `{ type, full_text, message_id }` | Agent finished responding |
| `agent_audio_chunk` | `{ type, audio: "<base64 PCM float32 24kHz>", message_id, segment_index }` | TTS audio for one sentence |
| `agent_audio_done` | `{ type, message_id }` | All audio segments sent |
| `tool_start` | `{ type, tool_name, tool_input, message_id }` | Agent called Brave Search |
| `tool_result` | `{ type, tool_name, result_summary, message_id }` | Search results returned |
| `heartbeat_start` | `{ type, heartbeat_name, message_id }` | A heartbeat is firing |
| `error` | `{ type, detail }` | Something went wrong |
| `pong` | `{ type }` | Response to ping, or initial ready signal |

All messages related to one conversational turn share the same `message_id`.

### Agent Architecture

The agent uses a LangGraph `StateGraph` with a standard ReAct tool-calling loop:

```
START
  │
  ▼
call_model ──► should_continue?
                 │            │
             has tool      no tool
              calls         calls
                 │            │
                 ▼            ▼
              tools          END
                 │
                 └──► call_model (loop)
```

**System prompt highlights:**
- Instructs conversational, voice-friendly responses (contractions, no markdown, 1-3 sentences)
- Requires the agent to say *"Hold on, let me check that out"* before every web search
- Injects retrieved memory context dynamically each turn
- For heartbeats, appends a `[HEARTBEAT]` instruction and accepts `[SILENT]` as a valid no-op response

**LLM configuration:** Uses `langchain-openai`'s `ChatOpenAI` with a configurable `base_url`. This means any OpenAI-compatible API works — Ollama, OpenAI, Anthropic proxy, LM Studio, vLLM, etc.

### Memory System

Every conversation exchange is stored in two places:

**1. Markdown files** — Human-readable, grep-able, version-controllable:
```
memory/conversations/2026-02-17.md
```
```markdown
# 2026-02-17

## 09:15

**User:** What's the latest on Rust's cranelift backend?

**Assistant:** Hold on, let me check that out. [Searched: "Rust cranelift backend 2026"]
The cranelift backend has been making steady progress. It's now the default
for debug builds in recent nightly compilers.

---

## 14:30

**User:** How do I set up a FastAPI WebSocket?

**Assistant:** You create an async endpoint decorated with @app.websocket. The handler
receives a WebSocket object you call accept, receive, and send on.

---
```

**2. ChromaDB vectors** — For semantic retrieval:
- Each user+assistant pair is embedded and stored with date metadata
- On every new user message, the top 3 most similar past exchanges are retrieved
- Plus today's full conversation history is included as context

The agent sees relevant memories injected into its system prompt, making it naturally aware of past conversations without you having to remind it.

### Heartbeat System

Heartbeats are periodic background prompts that "whisper" into the agent's context, making it proactive. They run as `asyncio` tasks on the server, only when a WebSocket connection is active.

**How a heartbeat works:**
1. Timer fires (e.g., every 30 minutes)
2. Heartbeat pauses if user/agent is actively speaking
3. A `[HEARTBEAT]` system message is sent to the agent
4. The agent decides: say something, or respond with `[SILENT]`
5. If it speaks, the response goes through the normal TTS pipeline and appears in the transcript with a heart icon
6. If silent, nothing happens — the user never knows a heartbeat fired

**Default heartbeats:**

| Name | Interval | What it does |
|------|----------|-------------|
| **Time Awareness** | 30 min | Notices the time; may check in if you've been quiet or if it's late |
| **Memory Reflection** | 60 min | Reviews today's conversation for unresolved threads or forgotten action items |
| **Proactive Search** | 120 min | Searches for news or updates relevant to what you've been discussing |
| **Mood/Energy Check** | 45 min | Gently checks in on how you're doing based on conversation tone |

All heartbeats can be toggled, adjusted, edited, or supplemented with custom ones via the settings panel (gear icon in the UI) or by editing `memory/heartbeats.json` directly.

---

## Configuration Reference

### Environment Variables

All settings live in `.env` at the project root.

| Variable | Default | Description |
|----------|---------|-------------|
| `LLM_BASE_URL` | `http://localhost:11434/v1` | Base URL for the LLM API. Change this to point at any OpenAI-compatible endpoint. |
| `LLM_API_KEY` | `ollama` | API key for the LLM. Set to `ollama` for local Ollama (it doesn't check the key). |
| `LLM_MODEL` | `llama3.1` | Model name as recognized by the API. For Ollama, this is the model you pulled. |
| `BRAVE_SEARCH_API_KEY` | *(empty)* | Your Brave Search API key. Without this, web search is disabled but everything else works. |
| `STT_MODEL` | `distil-large-v3` | Which Whisper model variant to use. See [STT Model Options](#stt-model-options). |
| `TTS_MODEL` | `mlx-community/Kokoro-82M-bf16` | HuggingFace model ID for TTS. |
| `TTS_VOICE` | `af_heart` | Kokoro voice preset. See [TTS Voice Options](#tts-voice-options). |
| `MEMORY_DIR` | `../memory` | Directory for conversation logs, ChromaDB, and heartbeat config. Relative to `backend/`. |

### LLM Provider Options

The app uses `langchain-openai` with a configurable base URL, so any OpenAI-compatible API works:

**Ollama (default, fully local):**
```bash
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=llama3.1
```

**OpenAI:**
```bash
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-your-key-here
LLM_MODEL=gpt-4o
```

**LM Studio:**
```bash
LLM_BASE_URL=http://localhost:1234/v1
LLM_API_KEY=not-needed
LLM_MODEL=your-loaded-model
```

**vLLM / Text Generation Inference:**
```bash
LLM_BASE_URL=http://localhost:8080/v1
LLM_API_KEY=not-needed
LLM_MODEL=meta-llama/Llama-3.1-8B-Instruct
```

**Anthropic (via LiteLLM proxy or similar):**
```bash
LLM_BASE_URL=http://localhost:4000/v1
LLM_API_KEY=sk-ant-your-key
LLM_MODEL=claude-sonnet-4-5-20250929
```

### STT Model Options

All models are from the [Whisper family](https://github.com/openai/whisper), optimized for MLX:

| Model | Size | Speed | Accuracy | Best For |
|-------|------|-------|----------|----------|
| `tiny` | ~75 MB | Fastest | Low | Quick testing |
| `base` | ~140 MB | Fast | Fair | Low-resource machines |
| `small` | ~460 MB | Medium | Good | General use |
| `distil-large-v3` | ~1.5 GB | Fast | Excellent | **Recommended** (best speed/accuracy) |
| `large-v3` | ~3 GB | Slower | Best | Maximum accuracy |

Change in `.env`:
```bash
STT_MODEL=distil-large-v3
```

### TTS Voice Options

Kokoro ships with 54 voice presets. Some good options:

| Voice ID | Description |
|----------|-------------|
| `af_heart` | Warm, friendly American female **(default)** |
| `af_bella` | Clear, pleasant American female |
| `af_sarah` | Professional American female |
| `am_adam` | Warm American male |
| `am_michael` | Clear American male |
| `bf_emma` | British female |
| `bm_george` | British male |

Change in `.env`:
```bash
TTS_VOICE=am_adam
```

> See the [Kokoro repository](https://github.com/hexgrad/kokoro) for the full list of available voices.

---

## Using the Application

### Voice Mode

1. Open the app — the microphone is automatically active
2. **Speak naturally.** The pulsing orb turns blue when the VAD detects your voice
3. **Pause.** When you stop speaking, the VAD fires and sends your audio to the server
4. **Wait ~1-1.5 seconds.** You'll hear the assistant's voice and see the transcript update
5. **Keep going.** The conversation flows naturally, turn by turn

### Text Fallback

At the bottom of the left panel is a text input field. Type a message and press Enter or click Send. This bypasses the STT pipeline — the text goes directly to the agent.

Useful when:
- You're in a noisy environment
- You want to paste something (a URL, code snippet, etc.)
- Voice recognition is mishearing you

### Barge-In (Interruption)

If the assistant is speaking and you start talking:
1. The VAD detects your voice
2. Audio playback **immediately stops**
3. Your new utterance is captured and processed as the next turn

This creates a natural conversational flow where you can interrupt at any time.

### Configuring Heartbeats

Click the **gear icon** in the top-right of the voice panel to open heartbeat settings:

- **Toggle** each heartbeat on/off with the checkbox
- **Adjust the interval** (in minutes) — how often it fires
- **Edit the prompt** — the instruction whispered to the agent
- **Add custom heartbeats** — click "+ Add Heartbeat" and fill in the fields
- **Remove heartbeats** — click the X button
- Click **Save** to persist changes

Heartbeat configuration is saved to `memory/heartbeats.json`. You can also edit this file directly (the server reads it at connection time).

**Example custom heartbeat:**
```json
{
  "id": "news_check",
  "name": "Tech News",
  "prompt": "Search for the top tech news of the day and mention anything relevant to the user's recent interests. If nothing stands out, stay silent.",
  "interval_minutes": 180,
  "enabled": true
}
```

### Reading Your Memory Files

Conversation logs are plain markdown:

```bash
# Today's conversations
cat memory/conversations/$(date +%Y-%m-%d).md

# All conversations
ls memory/conversations/

# Search across all conversations
grep -r "Rust" memory/conversations/

# See how much memory the assistant has
du -sh memory/.chromadb/
```

The markdown files are designed to be human-readable. Open them in any text editor or markdown viewer.

---

## Project Structure

```
voice-chat/
├── .env.example                      # Template for environment variables
├── .env                              # Your actual config (git-ignored)
├── .gitignore
├── README.md
├── run.sh                            # One-command launcher (venv, deps, both servers)
│
├── backend/                          # Python backend
│   ├── pyproject.toml                # Python dependencies
│   ├── main.py                       # FastAPI app, /ws endpoint, /api/heartbeats, /api/health
│   ├── config.py                     # Loads settings from .env
│   ├── ws_handler.py                 # WebSocket lifecycle: receive audio → STT → Agent → TTS → send
│   ├── stt.py                        # Lightning Whisper MLX (lazy-loaded, runs in thread)
│   ├── tts.py                        # Kokoro via mlx-audio (lazy-loaded, runs in thread)
│   ├── agent.py                      # LangGraph StateGraph with tool-calling loop
│   ├── tools.py                      # Brave Search tool definition
│   ├── memory.py                     # ChromaDB vectors + markdown file read/write
│   ├── heartbeat.py                  # Periodic proactive prompt scheduler
│   └── protocol.py                   # WebSocket message dataclasses + serialization
│
├── frontend/                         # React frontend
│   ├── index.html                    # HTML entry point (loads Inter font)
│   ├── package.json                  # Node dependencies
│   ├── tsconfig.json                 # TypeScript config
│   ├── vite.config.ts                # Vite config (React plugin, VAD asset copy, dev proxy)
│   ├── public/
│   │   └── vad/                      # Silero VAD ONNX model + WASM files (copied at build)
│   └── src/
│       ├── main.tsx                  # React DOM entry point
│       ├── App.tsx                   # Root component: initializes VAD, renders two-panel layout
│       ├── types.ts                  # All TypeScript types (WS messages, store shapes)
│       ├── hooks/
│       │   ├── useVoiceChat.ts       # Orchestrator: VAD → WAV encode → WS → state transitions
│       │   ├── useWebSocket.ts       # WS connection with exponential backoff reconnect
│       │   └── useAudioPlayback.ts   # Web Audio API gapless queue playback (24kHz)
│       ├── components/
│       │   ├── VoicePanel.tsx        # Left panel: orb, status, mic toggle, text input, settings
│       │   ├── VoiceOrb.tsx          # Canvas-based pulsing orb visualization
│       │   ├── TranscriptPanel.tsx   # Right panel: scrollable message list
│       │   ├── TranscriptMessage.tsx # Single message: role, text, timestamp, tool cards
│       │   ├── StatusIndicator.tsx   # Connection dot + state text
│       │   └── HeartbeatSettings.tsx # Heartbeat CRUD UI (toggle, interval, prompt, add/remove)
│       ├── stores/
│       │   └── chatStore.ts          # Zustand store: messages[], appState, isConnected
│       └── styles/
│           └── global.css            # Dark theme CSS (~280 lines)
│
└── memory/                           # Persistent memory (created at runtime)
    ├── conversations/                # Daily markdown conversation logs
    │   └── 2026-02-17.md
    ├── .chromadb/                     # ChromaDB vector database (git-ignored)
    └── heartbeats.json               # Heartbeat configuration (git-ignored)
```

---

## Resource Usage

Estimated memory usage on Apple Silicon:

| Component | RAM | Notes |
|-----------|-----|-------|
| Whisper distil-large-v3 | ~1.5 GB | Loaded on first voice interaction |
| Kokoro 82M (bf16) | ~170 MB | Loaded on first agent response |
| Ollama llama3.1 (8B, Q4) | ~5 GB | Managed by Ollama, loaded on first query |
| ChromaDB + embeddings | ~200 MB | Grows with conversation history |
| Python process overhead | ~300 MB | FastAPI + asyncio + dependencies |
| Browser tab | ~200 MB | React + VAD ONNX model |
| **Total** | **~7.5 GB** | On a 64 GB M4 Max, leaves ~56 GB free |

> STT and TTS models are loaded lazily — only when the first audio arrives. This means the server starts instantly during development.

---

## Troubleshooting

### "Connection refused" or WebSocket won't connect

**Cause:** Backend isn't running.
```bash
# Check if the backend is listening
curl http://localhost:8000/api/health
# Should return: {"status":"ok"}

# If not, start it:
./run.sh backend
# Or manually:
source backend/.venv/bin/activate && cd backend && uvicorn main:app --host 0.0.0.0 --port 8000
```

### "Ollama not reachable" / LLM errors

**Cause:** Ollama service isn't running or model not pulled.
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags
# Should list your pulled models

# If not running:
ollama serve

# If model not pulled:
ollama pull llama3.1
```

### No audio plays back / TTS errors in server log

**Cause:** TTS model download failed or mlx-audio not installed correctly.
```bash
# Verify mlx-audio is installed
source backend/.venv/bin/activate
python3 -c "from mlx_audio.tts.generate import generate_speech; print('OK')"

# If it fails, reinstall:
source backend/.venv/bin/activate
pip install --force-reinstall mlx-audio
```

### STT returns empty transcripts

**Cause:** Audio is too short, too quiet, or the model failed to load.
```bash
# Test STT directly
source backend/.venv/bin/activate
python3 -c "
from lightning_whisper_mlx import LightningWhisperMLX
w = LightningWhisperMLX(model='distil-large-v3', batch_size=12)
print('STT model loaded successfully')
"
```

Also check:
- Your microphone is working (test in System Settings > Sound)
- You allowed microphone access in the browser
- You're speaking loudly enough for VAD to trigger

### Browser microphone permission denied

1. Click the lock/site-settings icon in the URL bar
2. Set Microphone to **Allow**
3. Reload the page

### "Brave Search API key not configured"

The assistant will say this if `BRAVE_SEARCH_API_KEY` is empty in `.env`. This is not fatal — everything else works, the agent just can't search the web.

### Models downloading slowly

First-run model downloads happen over HuggingFace:
- STT (distil-large-v3): ~1.5 GB
- TTS (Kokoro-82M-bf16): ~170 MB

These are cached after the first download. If downloads are slow, check your internet connection or try setting a HuggingFace mirror.

### Port already in use

```bash
# Find what's using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8001
# Also update vite.config.ts proxy target to match
```

### Frontend build errors about VAD files

The Vite config copies VAD model files from `node_modules` at build time. If you see 404 errors for `/vad/*.onnx`:
```bash
cd frontend
rm -rf node_modules
npm install
npm run dev
```

---

## Development

### Backend hot-reload

```bash
# Using run.sh (activates venv automatically):
./run.sh backend
# Then Ctrl+C and restart — or use --reload directly:

# Manual with hot-reload:
source backend/.venv/bin/activate
cd backend
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

The `--reload` flag watches for file changes and restarts the server. Models stay lazy-loaded, so restarts are fast. The venv at `backend/.venv` is always used — never install packages globally.

### Frontend hot-reload

Vite provides HMR (Hot Module Replacement) out of the box:
```bash
cd frontend
npm run dev
```

Code changes reflect instantly in the browser without a full page reload.

### Dev proxy

The Vite config proxies `/ws` and `/api` requests to `localhost:8000`, so the frontend and backend can run on different ports during development without CORS issues.

### Adding a new tool

1. Define the tool in `backend/tools.py` using the `@tool` decorator
2. Add it to the `tools` list in `backend/agent.py`
3. Optionally update the system prompt in `backend/agent.py` to instruct the agent on when/how to use it

### Modifying the system prompt

Edit `SYSTEM_PROMPT` in `backend/agent.py`. The prompt supports two format variables:
- `{current_date}` — injected automatically each turn
- `{memory_context}` — injected from ChromaDB retrieval + today's conversation history

### Adding a new heartbeat programmatically

Edit `DEFAULT_HEARTBEATS` in `backend/heartbeat.py`, or add an entry to `memory/heartbeats.json`:
```json
{
  "id": "your_id",
  "name": "Display Name",
  "prompt": "Instructions for the agent...",
  "interval_minutes": 60,
  "enabled": true
}
```

### Building for production

```bash
cd frontend
npm run build
# Output in frontend/dist/

# Serve with any static file server, or configure FastAPI to serve it:
# In backend/main.py, add:
# from fastapi.staticfiles import StaticFiles
# app.mount("/", StaticFiles(directory="../frontend/dist", html=True))
```
