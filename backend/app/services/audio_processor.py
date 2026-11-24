import logging
import subprocess
import tempfile
import os
import numpy as np
from typing import Optional

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Minimal audio format conversion utility."""

    @staticmethod
    def pcm16_to_float32(pcm_bytes: bytes) -> np.ndarray:
        if len(pcm_bytes) % 2 != 0:
            pcm_bytes = pcm_bytes[: len(pcm_bytes) - 1]
        if not pcm_bytes:
            return np.array([], dtype=np.float32)
        return np.frombuffer(pcm_bytes, dtype=np.int16).astype(np.float32) / 32768.0

    @staticmethod
    def webm_to_pcm_float32(webm_data: bytes, target_sr: int = 16000) -> Optional[np.ndarray]:
        """Convert WebM/Opus from browser to float32 PCM via ffmpeg."""
        if len(webm_data) < 100:
            return None
        tmp = None
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".webm", delete=False)
            tmp.write(webm_data)
            tmp.flush()
            tmp.close()

            result = subprocess.run(
                ["ffmpeg", "-y", "-i", tmp.name,
                 "-f", "s16le", "-acodec", "pcm_s16le",
                 "-ar", str(target_sr), "-ac", "1", "pipe:1"],
                capture_output=True, timeout=30,
            )
            if result.returncode != 0:
                logger.error("ffmpeg error: %s", result.stderr.decode(errors="ignore")[:200])
                return None

            return AudioProcessor.pcm16_to_float32(result.stdout)
        except Exception as e:
            logger.error("Audio conversion failed: %s", e)
            return None
        finally:
            if tmp and os.path.exists(tmp.name):
                try:
                    os.unlink(tmp.name)
                except Exception:
                    pass

    @staticmethod
    def detect_format(data: bytes) -> str:
        if len(data) >= 4:
            if data[:4] == b"RIFF":
                return "wav"
            if data[:4] == b"\x1aE\xdf\xa3":
                return "webm"
        return "pcm"
