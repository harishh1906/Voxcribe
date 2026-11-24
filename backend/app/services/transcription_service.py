from typing import Optional
from sqlalchemy import func, or_, desc, asc
from sqlalchemy.orm import Session
from app.models.transcription import Transcription
from app.schemas.transcription import (
    TranscriptionCreate,
    TranscriptionUpdate,
    TranscriptionResponse,
    TranscriptionListResponse,
    DashboardStats,
)


def get_transcription(db: Session, transcription_id: str) -> Optional[Transcription]:
    return db.query(Transcription).filter(Transcription.id == transcription_id).first()


def get_transcriptions(
    db: Session,
    page: int = 1,
    page_size: int = 20,
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
) -> TranscriptionListResponse:
    query = db.query(Transcription)

    if search:
        query = query.filter(
            or_(
                Transcription.title.ilike(f"%{search}%"),
                Transcription.transcription_text.ilike(f"%{search}%"),
            )
        )

    sort_col = getattr(Transcription, sort_by, Transcription.created_at)
    query = query.order_by(desc(sort_col) if sort_order == "desc" else asc(sort_col))

    total = query.count()
    items = query.offset((page - 1) * page_size).limit(page_size).all()

    return TranscriptionListResponse(
        items=[TranscriptionResponse.model_validate(i) for i in items],
        total=total,
        page=page,
        page_size=page_size,
    )


def create_transcription(db: Session, data: TranscriptionCreate) -> Transcription:
    word_count = len(data.transcription_text.split()) if data.transcription_text else 0
    t = Transcription(
        title=data.title,
        transcription_text=data.transcription_text,
        language_detected=data.language_detected,
        duration_seconds=data.duration_seconds,
        word_count=word_count,
    )
    db.add(t)
    db.commit()
    db.refresh(t)
    return t


def update_transcription(
    db: Session, transcription_id: str, data: TranscriptionUpdate
) -> Optional[Transcription]:
    t = get_transcription(db, transcription_id)
    if not t:
        return None
    if data.title is not None:
        t.title = data.title
    if data.transcription_text is not None:
        t.transcription_text = data.transcription_text
        t.word_count = len(data.transcription_text.split()) if data.transcription_text else 0
    db.commit()
    db.refresh(t)
    return t


def delete_transcription(db: Session, transcription_id: str) -> bool:
    t = get_transcription(db, transcription_id)
    if not t:
        return False
    db.delete(t)
    db.commit()
    return True


def get_dashboard_stats(db: Session) -> DashboardStats:
    total = db.query(func.count(Transcription.id)).scalar() or 0
    total_dur = db.query(func.sum(Transcription.duration_seconds)).scalar() or 0.0
    total_words = db.query(func.sum(Transcription.word_count)).scalar() or 0
    avg_dur = db.query(func.avg(Transcription.duration_seconds)).scalar() or 0.0

    recent = (
        db.query(Transcription)
        .order_by(desc(Transcription.created_at))
        .limit(5)
        .all()
    )

    # Language distribution
    lang_rows = (
        db.query(Transcription.language_detected, func.count(Transcription.id))
        .group_by(Transcription.language_detected)
        .all()
    )
    lang_dist = {lang or "Unknown": count for lang, count in lang_rows}

    return DashboardStats(
        total_transcriptions=total,
        total_duration=round(float(total_dur), 1),
        total_words=int(total_words),
        avg_duration=round(float(avg_dur), 1),
        recent_transcriptions=[TranscriptionResponse.model_validate(r) for r in recent],
        language_distribution=lang_dist,
    )
