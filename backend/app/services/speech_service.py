import asyncio
import logging
import re
import numpy as np
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

_whisper_available = False
try:
    from faster_whisper import WhisperModel
    _whisper_available = True
except Exception as e:
    logger.warning("faster-whisper not available: %s. Transcription will be disabled.", e)


# --- Anti-hallucination helpers ---

def _is_repetitive(text: str, threshold: int = 4) -> bool:
    """Detect if text is mostly a single word/phrase repeated many times."""
    if not text:
        return False
    words = text.split()
    if len(words) < threshold:
        return False
    # Check if any single token makes up > 60% of the words
    from collections import Counter
    counts = Counter(words)
    most_common_word, most_common_count = counts.most_common(1)[0]
    if most_common_count / len(words) > 0.6:
        logger.debug("Repetitive text detected: '%s' repeated %d/%d times", most_common_word, most_common_count, len(words))
        return True
    # Check for repeating bigrams
    if len(words) >= 6:
        bigrams = [words[i] + " " + words[i + 1] for i in range(len(words) - 1)]
        bg_counts = Counter(bigrams)
        top_bg, top_bg_count = bg_counts.most_common(1)[0]
        if top_bg_count / len(bigrams) > 0.5:
            logger.debug("Repetitive bigram detected: '%s' repeated %d times", top_bg, top_bg_count)
            return True
    return False


def _is_hallucination(text: str) -> bool:
    """Detect common Whisper hallucination patterns."""
    if not text:
        return False
    stripped = text.strip()
    # All ellipsis / dots / dashes
    if re.fullmatch(r'[.\s…\-–—]+', stripped):
        return True
    # Very short garbage (single punctuation, single foreign char, etc.)
    if len(stripped) <= 2 and not stripped.isalnum():
        return True
    # Common Whisper hallucination phrases
    hallucination_phrases = [
        "thank you for watching",
        "thanks for watching",
        "please subscribe",
        "like and subscribe",
        "subtitles by",
        "translated by",
        "amara.org",
    ]
    lower = stripped.lower()
    for phrase in hallucination_phrases:
        if phrase in lower:
            return True
    return False


def _clean_text(text: str) -> str:
    """Remove leading/trailing noise characters from transcribed text."""
    # Strip leading/trailing ellipsis, dots, dashes, spaces
    cleaned = re.sub(r'^[.\s…\-–—,;:]+', '', text)
    cleaned = re.sub(r'[.\s…\-–—,;:]+$', '', cleaned)
    return cleaned.strip()


class SpeechRecognitionService:
    """Singleton service wrapping Faster-Whisper for real-time transcription."""

    _instance: Optional["SpeechRecognitionService"] = None
    _model = None

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
        """Load Faster-Whisper model in a background thread."""
        self.model_name = model_name
        self.device = device
        self.compute_type = compute_type

        if not _whisper_available:
            logger.warning("Whisper not available — skipping model load.")
            return

        try:
            await asyncio.to_thread(self._load_sync, model_name, device, compute_type)
            self.model_loaded = True
            logger.info("Whisper model '%s' loaded on %s (%s)", model_name, device, compute_type)
        except Exception as e:
            logger.error("Failed to load Whisper model: %s", e)
            self.model_loaded = False

    def _load_sync(self, model_name: str, device: str, compute_type: str):
        from app.config import get_settings
        _settings = get_settings()
        SpeechRecognitionService._model = WhisperModel(
            model_name, device=device, compute_type=compute_type,
            cpu_threads=_settings.WHISPER_CPU_THREADS,
        )

    async def transcribe(self, audio: np.ndarray, sample_rate: int = 16000) -> Dict[str, Any]:
        """Transcribe a float32 numpy audio array."""
        if not self.model_loaded or self._model is None:
            return {
                "text": "",
                "language": None,
                "segments": [],
                "error": "Model not loaded",
            }
        try:
            return await asyncio.to_thread(self._transcribe_sync, audio, sample_rate)
        except Exception as e:
            logger.error("Transcription error: %s", e)
            return {"text": "", "language": None, "segments": [], "error": str(e)}

    def _transcribe_sync(self, audio: np.ndarray, sample_rate: int) -> Dict[str, Any]:
        if len(audio) == 0:
            return {"text": "", "language": None, "language_probability": 0.0, "segments": []}

        rms = float(np.sqrt(np.mean(audio ** 2)))
        logger.info("Transcribe called: samples=%d (%.2fs), rms=%.5f", len(audio), len(audio) / sample_rate, rms)

        # 0.0015 threshold allows normal spoken volume while gating absolute silence
        if rms < 0.0015:
            logger.info("Audio below silence threshold (rms=%.5f < 0.0015), skipping", rms)
            return {"text": "", "language": None, "language_probability": 0.0, "segments": []}

        try:
            from app.config import get_settings
            _settings = get_settings()
            segments_iter, info = self._model.transcribe(
                audio,
                beam_size=_settings.WHISPER_BEAM_SIZE,
                language=None,  # auto-detect (Hindi, English, Hinglish)
                vad_filter=False,  # disabled to prevent empty-sequence crash
                condition_on_previous_text=False,
                temperature=0.0,
            )

            text_parts = []
            seg_list = []
            for seg in segments_iter:
                seg_text = seg.text.strip()
                if _is_hallucination(seg_text):
                    continue
                text_parts.append(seg.text)
                seg_list.append({"start": seg.start, "end": seg.end, "text": seg.text})

            full_text = "".join(text_parts).strip()
            full_text = _clean_text(full_text)
            if _is_hallucination(full_text):
                full_text = ""

            lang = getattr(info, "language", None)
            prob = getattr(info, "language_probability", 0.0)
            lang_prob = round(prob, 2) if prob is not None else 0.0

            logger.info("Transcription result: text='%s', lang=%s (%.2f)", full_text, lang, lang_prob)

            return {
                "text": full_text,
                "language": lang,
                "language_probability": lang_prob,
                "segments": seg_list,
            }
        except ValueError as e:
            if "empty sequence" in str(e):
                return {"text": "", "language": None, "language_probability": 0.0, "segments": []}
            raise

    def get_info(self) -> Dict[str, Any]:
        return {
            "model_loaded": self.model_loaded,
            "model_name": self.model_name,
            "device": self.device,
            "compute_type": self.compute_type,
            "whisper_available": _whisper_available,
        }
