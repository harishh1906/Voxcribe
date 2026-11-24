import io
import logging
import subprocess
import tempfile
import os
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Utility class for audio format conversions."""

    @staticmethod
    def pcm16_to_float32(pcm_bytes: bytes) -> np.ndarray:
        """Convert 16-bit signed PCM bytes to float32 array in [-1, 1]."""
        if len(pcm_bytes) % 2 != 0:
            pcm_bytes = pcm_bytes[:len(pcm_bytes) - 1]
        if len(pcm_bytes) == 0:
            return np.array([], dtype=np.float32)
        audio = np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32)
        return audio / 32768.0

    @staticmethod
    def normalize(audio: np.ndarray) -> np.ndarray:
        if len(audio) == 0:
            return audio
        peak = np.max(np.abs(audio))
        if peak > 0:
            return audio / peak
        return audio

    @staticmethod
    def is_silence(audio: np.ndarray, threshold: float = 0.003) -> bool:
        """Check if audio energy is below silence threshold."""
        if len(audio) == 0:
            return True
        rms = np.sqrt(np.mean(audio ** 2))
        return bool(rms < threshold)

    @staticmethod
    def webm_to_pcm_float32(webm_data: bytes, target_sr: int = 16000) -> Optional[np.ndarray]:
        """Convert WebM/Opus bytes from browser MediaRecorder to float32 PCM via ffmpeg."""
        if len(webm_data) < 100:
            return None
        tmp_in = None
        try:
            tmp_in = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
            tmp_in.write(webm_data)
            tmp_in.flush()
            tmp_in.close()

            cmd = [
                "ffmpeg", "-y", "-i", tmp_in.name,
                "-f", "s16le", "-acodec", "pcm_s16le",
                "-ar", str(target_sr), "-ac", "1",
                "pipe:1",
            ]
            result = subprocess.run(
                cmd, capture_output=True, timeout=15,
            )
            if result.returncode != 0:
                logger.error("ffmpeg error (code %d): %s", result.returncode, result.stderr.decode(errors="ignore")[:300])
                return None

            return AudioProcessor.pcm16_to_float32(result.stdout)
        except Exception as e:
            logger.error("Audio conversion failed: %s", e)
            return None
        finally:
            if tmp_in and os.path.exists(tmp_in.name):
                try:
                    os.unlink(tmp_in.name)
                except Exception:
                    pass

    @staticmethod
    def detect_format(data: bytes) -> str:
        """Detect audio format from magic bytes."""
        if len(data) >= 4:
            if data[:4] == b"RIFF":
                return "wav"
            if data[:4] == b"\x1aE\xdf\xa3":
                return "webm"
        return "pcm"
