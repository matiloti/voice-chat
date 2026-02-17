"""Application settings loaded from environment / .env file."""

import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env from project root
_project_root = Path(__file__).resolve().parent.parent
_env_path = _project_root / ".env"
load_dotenv(_env_path)


class Settings:
    # LLM
    llm_base_url: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
    llm_api_key: str = os.getenv("LLM_API_KEY", "ollama")
    llm_model: str = os.getenv("LLM_MODEL", "llama3.1")

    # Brave Search
    brave_search_api_key: str = os.getenv("BRAVE_SEARCH_API_KEY", "")

    # STT
    stt_model: str = os.getenv("STT_MODEL", "distil-large-v3")

    # TTS
    tts_model: str = os.getenv("TTS_MODEL", "mlx-community/Kokoro-82M-bf16")
    tts_voice: str = os.getenv("TTS_VOICE", "af_heart")

    # Memory
    memory_dir: Path = Path(os.getenv("MEMORY_DIR", str(_project_root / "memory")))

    @property
    def conversations_dir(self) -> Path:
        d = self.memory_dir / "conversations"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def chromadb_dir(self) -> Path:
        d = self.memory_dir / ".chromadb"
        d.mkdir(parents=True, exist_ok=True)
        return d

    @property
    def heartbeats_path(self) -> Path:
        return self.memory_dir / "heartbeats.json"


settings = Settings()
