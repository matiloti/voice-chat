"""Speech-to-Text engine using Lightning Whisper MLX."""

import asyncio
import io
import struct
import logging
import numpy as np

from config import settings

logger = logging.getLogger(__name__)


class STTEngine:
    """Lazy-loading Whisper STT wrapper."""

    def __init__(self) -> None:
        self._model = None

    def _ensure_loaded(self) -> None:
        if self._model is not None:
            return
        logger.info("Loading STT model: %s (this may take a moment on first run)...", settings.stt_model)
        from lightning_whisper_mlx import LightningWhisperMLX
        self._model = LightningWhisperMLX(model=settings.stt_model, batch_size=12, quant=None)
        logger.info("STT model loaded.")

    def _decode_wav_bytes(self, wav_bytes: bytes) -> np.ndarray:
        """Decode WAV bytes to float32 numpy array at original sample rate."""
        buf = io.BytesIO(wav_bytes)

        # Read WAV header
        riff = buf.read(4)
        if riff != b"RIFF":
            raise ValueError("Not a valid WAV file")
        buf.read(4)  # file size
        wave = buf.read(4)
        if wave != b"WAVE":
            raise ValueError("Not a valid WAV file")

        # Read chunks
        sample_rate = 16000
        num_channels = 1
        bits_per_sample = 16
        audio_data = b""

        while True:
            chunk_id = buf.read(4)
            if len(chunk_id) < 4:
                break
            chunk_size = struct.unpack("<I", buf.read(4))[0]

            if chunk_id == b"fmt ":
                fmt_data = buf.read(chunk_size)
                num_channels = struct.unpack("<H", fmt_data[2:4])[0]
                sample_rate = struct.unpack("<I", fmt_data[4:8])[0]
                bits_per_sample = struct.unpack("<H", fmt_data[14:16])[0]
            elif chunk_id == b"data":
                audio_data = buf.read(chunk_size)
            else:
                buf.read(chunk_size)

        # Convert to float32
        if bits_per_sample == 16:
            samples = np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
        elif bits_per_sample == 32:
            samples = np.frombuffer(audio_data, dtype=np.float32)
        else:
            raise ValueError(f"Unsupported bits per sample: {bits_per_sample}")

        # Convert to mono if stereo
        if num_channels > 1:
            samples = samples.reshape(-1, num_channels).mean(axis=1)

        return samples

    def _transcribe_sync(self, wav_bytes: bytes) -> str:
        """Synchronous transcription. Called from asyncio.to_thread."""
        self._ensure_loaded()
        audio = self._decode_wav_bytes(wav_bytes)

        # Use the underlying transcribe method
        # LightningWhisperMLX.transcribe calls transcribe_audio which accepts numpy arrays
        import tempfile
        import os
        # Write to temp file since the library expects file paths
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as f:
            # Write a proper WAV file from our numpy array
            self._write_wav(f, audio, 16000)
            tmp_path = f.name

        try:
            result = self._model.transcribe(tmp_path)
            return result.get("text", "").strip()
        finally:
            os.unlink(tmp_path)

    def _write_wav(self, f: io.IOBase, audio: np.ndarray, sample_rate: int) -> None:
        """Write numpy float32 array as WAV file."""
        pcm16 = (audio * 32767).astype(np.int16)
        data = pcm16.tobytes()

        # WAV header
        f.write(b"RIFF")
        f.write(struct.pack("<I", 36 + len(data)))
        f.write(b"WAVE")
        f.write(b"fmt ")
        f.write(struct.pack("<I", 16))  # chunk size
        f.write(struct.pack("<H", 1))   # PCM
        f.write(struct.pack("<H", 1))   # mono
        f.write(struct.pack("<I", sample_rate))
        f.write(struct.pack("<I", sample_rate * 2))  # byte rate
        f.write(struct.pack("<H", 2))   # block align
        f.write(struct.pack("<H", 16))  # bits per sample
        f.write(b"data")
        f.write(struct.pack("<I", len(data)))
        f.write(data)

    async def transcribe(self, wav_bytes: bytes) -> str:
        """Transcribe WAV audio bytes to text. Runs inference in a thread."""
        return await asyncio.to_thread(self._transcribe_sync, wav_bytes)
