import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Text, Float, Integer, DateTime
from app.database import Base


class Transcription(Base):
    __tablename__ = "transcriptions"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(255), nullable=False, default="Untitled Recording")
    transcription_text = Column(Text, nullable=False, default="")
    language_detected = Column(String(50), nullable=True)
    duration_seconds = Column(Float, default=0.0)
    word_count = Column(Integer, default=0)
    status = Column(String(20), default="completed")
    audio_file_path = Column(String(500), nullable=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), onupdate=lambda: datetime.now(timezone.utc))

    def __repr__(self):
        return f"<Transcription {self.id}: {self.title}>"
