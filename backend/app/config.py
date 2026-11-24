from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://postgres:postgres@db:5432/voxcribe"

    # Whisper
    WHISPER_MODEL: str = "MSpider3/whisper-hindi2hinglish-swift-ct2"
    WHISPER_DEVICE: str = "cpu"
    WHISPER_COMPUTE_TYPE: str = "int8"
    WHISPER_BEAM_SIZE: int = 1
    WHISPER_CPU_THREADS: int = 2
    WHISPER_LANGUAGE: Optional[str] = "en"
    WHISPER_INITIAL_PROMPT: Optional[str] = None

    # Audio
    VAD_THRESHOLD: float = 0.5
    AUDIO_CHUNK_DURATION: float = 3.0
    AUDIO_OVERLAP_DURATION: float = 0.5
    AUDIO_SAMPLE_RATE: int = 16000
    MAX_RECORDING_DURATION: int = 3600
    STORE_AUDIO_FILES: bool = False

    # App
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000", "http://localhost:80"]
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
