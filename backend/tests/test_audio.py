import numpy as np
from app.services.audio_processor import AudioProcessor


def test_pcm16_to_float32():
    pcm = np.array([0, 16384, -16384, 32767], dtype=np.int16).tobytes()
    result = AudioProcessor.pcm16_to_float32(pcm)
    assert result.dtype == np.float32
    assert len(result) == 4
    assert abs(result[0]) < 0.001
    assert abs(result[1] - 0.5) < 0.01


def test_normalize():
    audio = np.array([0.0, 0.5, -0.5], dtype=np.float32)
    normed = AudioProcessor.normalize(audio)
    assert abs(normed[1] - 1.0) < 0.001


def test_detect_format_pcm():
    assert AudioProcessor.detect_format(b"\x00\x01\x02\x03") == "pcm"


def test_detect_format_wav():
    assert AudioProcessor.detect_format(b"RIFF\x00\x00\x00\x00WAVE") == "wav"


def test_detect_format_webm():
    assert AudioProcessor.detect_format(b"\x1aE\xdf\xa3\x00\x00") == "webm"
