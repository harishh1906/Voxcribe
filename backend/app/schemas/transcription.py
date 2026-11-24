from datetime import datetime
from typing import Optional, List, Dict
from pydantic import BaseModel, ConfigDict


class TranscriptionCreate(BaseModel):
    title: str = "Untitled Recording"
    transcription_text: str = ""
    language_detected: Optional[str] = None
    duration_seconds: float = 0.0


class TranscriptionUpdate(BaseModel):
    title: Optional[str] = None
    transcription_text: Optional[str] = None


class TranscriptionResponse(BaseModel):
    id: str
    title: str
    transcription_text: str
    language_detected: Optional[str]
    duration_seconds: float
    word_count: int
    status: str
    audio_file_path: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class TranscriptionListResponse(BaseModel):
    items: List[TranscriptionResponse]
    total: int
    page: int
    page_size: int


class DashboardStats(BaseModel):
    total_transcriptions: int
    total_duration: float
    total_words: int
    avg_duration: float
    recent_transcriptions: List[TranscriptionResponse]
    language_distribution: Dict[str, int]
