from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.schemas.transcription import (
    TranscriptionCreate,
    TranscriptionUpdate,
    TranscriptionResponse,
    TranscriptionListResponse,
    DashboardStats,
)
from app.services import transcription_service as svc

router = APIRouter(prefix="/api/transcriptions", tags=["transcriptions"])


@router.get("/stats/dashboard", response_model=DashboardStats)
def dashboard_stats(db: Session = Depends(get_db)):
    return svc.get_dashboard_stats(db)


@router.get("", response_model=TranscriptionListResponse, include_in_schema=False)
@router.get("/", response_model=TranscriptionListResponse)
def list_transcriptions(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    search: Optional[str] = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
    db: Session = Depends(get_db),
):
    return svc.get_transcriptions(db, page, page_size, search, sort_by, sort_order)


@router.get("/{transcription_id}", response_model=TranscriptionResponse)
def get_transcription(transcription_id: str, db: Session = Depends(get_db)):
    t = svc.get_transcription(db, transcription_id)
    if not t:
        raise HTTPException(404, "Transcription not found")
    return t


@router.post("", response_model=TranscriptionResponse, status_code=201, include_in_schema=False)
@router.post("/", response_model=TranscriptionResponse, status_code=201)
def create_transcription(data: TranscriptionCreate, db: Session = Depends(get_db)):
    return svc.create_transcription(db, data)


@router.put("/{transcription_id}", response_model=TranscriptionResponse)
def update_transcription(
    transcription_id: str, data: TranscriptionUpdate, db: Session = Depends(get_db)
):
    t = svc.update_transcription(db, transcription_id, data)
    if not t:
        raise HTTPException(404, "Transcription not found")
    return t


@router.delete("/{transcription_id}")
def delete_transcription(transcription_id: str, db: Session = Depends(get_db)):
    if not svc.delete_transcription(db, transcription_id):
        raise HTTPException(404, "Transcription not found")
    return {"message": "Transcription deleted"}
