"""Text-to-Speech engine using Kokoro via mlx-audio."""

import asyncio
import logging
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class TTSEngine:
    """Lazy-loading Kokoro TTS wrapper."""

    def __init__(self) -> None:
        self._model = None
        self._sample_rate = 24000

    @property
    def sample_rate(self) -> int:
        return self._sample_rate

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        logger.info("Loading TTS model: %s ...", settings.tts_model)
        from mlx_audio.tts.generate import load_model
        self._model = load_model(settings.tts_model)
        self._sample_rate = self._model.sample_rate
        logger.info("TTS model loaded (sample_rate=%d).", self._sample_rate)

    def _synthesize_sync(self, text: str) -> bytes:
        """Synchronous TTS generation. Returns raw PCM float32 bytes at 24kHz."""
        self._ensure_loaded()

        if not text.strip():
            return b""

        try:
            results = self._model.generate(
                text=text,
                voice=settings.tts_voice,
            )

            audio_parts = []
            for result in results:
                audio_np = np.array(result.audio, dtype=np.float32)
                if audio_np.ndim > 1:
                    audio_np = audio_np.flatten()
                audio_parts.append(audio_np)

            if not audio_parts:
                return b""

            audio = np.concatenate(audio_parts) if len(audio_parts) > 1 else audio_parts[0]
            return audio.tobytes()

        except Exception as e:
            logger.error("TTS synthesis failed: %s", e)
            return b""

    async def synthesize(self, text: str) -> bytes:
        """Synthesize text to PCM float32 audio bytes at 24kHz. Runs in a thread."""
        return await asyncio.to_thread(self._synthesize_sync, text)
