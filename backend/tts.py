"""Text-to-Speech engine using Kokoro via mlx-audio."""

import asyncio
import logging
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class TTSEngine:
    """Lazy-loading Kokoro TTS wrapper."""

    def __init__(self) -> None:
        self._pipeline = None
        self._sample_rate = 24000

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def _ensure_loaded(self) -> None:
        if self._pipeline is not None:
            return
        logger.info("Loading TTS model: %s ...", settings.tts_model)
        from mlx_audio.tts.generate import generate_speech
        # Store the generate function — we'll call it per sentence
        self._generate = generate_speech
        self._pipeline = True  # Mark as loaded
        logger.info("TTS model loaded.")

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous TTS generation. Returns raw PCM float32 bytes at 24kHz."""
        self._ensure_loaded()

        if not text.strip():
            return b""

        try:
            # mlx-audio generate_speech returns audio array
            audio = self._generate(
                text=text,
                model_id_or_path=settings.tts_model,
                voice=settings.tts_voice,
            )

            # Convert to numpy float32
            if hasattr(audio, "numpy"):
                audio_np = np.array(audio, dtype=np.float32)
            elif isinstance(audio, np.ndarray):
                audio_np = audio.astype(np.float32)
            else:
                audio_np = np.array(audio, dtype=np.float32)

            # Flatten if needed
            if audio_np.ndim > 1:
                audio_np = audio_np.flatten()

            return audio_np.tobytes()

        except Exception as e:
            logger.error("TTS synthesis failed: %s", e)
            return b""

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to PCM float32 audio bytes at 24kHz. Runs in a thread."""
        return await asyncio.to_thread(self._synthesize_sync, text)
