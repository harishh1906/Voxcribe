import asyncio
import logging
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

_whisper_available = False
try:
    from faster_whisper import WhisperModel
    _whisper_available = True
except Exception as e:
    logger.warning("faster-whisper not available: %s", e)


class SpeechRecognitionService:
    """Minimal Faster-Whisper wrapper — audio in, text out."""

    _instance: Optional["SpeechRecognitionService"] = None
    _model: Optional["WhisperModel"] = None

    def __init__(self):
        self.model_loaded = False
        self.model_name = ""
        self.device = ""
        self.compute_type = ""

    @classmethod
    def get_instance(cls) -> "SpeechRecognitionService":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def load_model(self, model_name: str, device: str = "cpu", compute_type: str = "int8"):
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type
        if not _whisper_available:
            return
        try:
            from app.config import get_settings
            settings = get_settings()
            logger.info("Loading model: %s on %s (%s)...", model_name, device, compute_type)
            SpeechRecognitionService._model = await asyncio.to_thread(
                WhisperModel, model_name, device=device,
                compute_type=compute_type, cpu_threads=settings.WHISPER_CPU_THREADS,
            )
            self.model_loaded = True
            logger.info("Model '%s' loaded.", model_name)
        except Exception as e:
            logger.error("Failed to load model: %s", e)
            self.model_loaded = False

    async def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        if not self.model_loaded or self._model is None or len(audio) == 0:
            return {"text": "", "language": None, "language_probability": 0.0}
        try:
            return await asyncio.to_thread(self._run, audio)
        except Exception as e:
            logger.error("Transcription error: %s", e)
            return {"text": "", "language": None, "language_probability": 0.0}

    def _run(self, audio: np.ndarray) -> Dict[str, Any]:
        from app.config import get_settings
        settings = get_settings()

        segments, info = self._model.transcribe(
            audio,
            language=settings.WHISPER_LANGUAGE,
            beam_size=settings.WHISPER_BEAM_SIZE,
            temperature=0.0,
            vad_filter=True,
        )

        text = " ".join(seg.text.strip() for seg in segments if seg.text.strip())
        lang = getattr(info, "language", None)
        prob = round(getattr(info, "language_probability", 0.0) or 0.0, 2)

        logger.info("Result: '%s'", text)
        return {"text": text, "language": lang, "language_probability": prob}

    def get_info(self) -> Dict[str, Any]:
        return {
            "model_loaded": self.model_loaded,
            "model_name": self.model_name,
            "device": self.device,
            "compute_type": self.compute_type,
            "whisper_available": _whisper_available,
        }
