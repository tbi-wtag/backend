import uuid
from datetime import date
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_db
from app.schemas.slot import SlotSearchResponse
from app.services import slot_service

router = APIRouter(prefix="/slots", tags=["Slots"])


@router.get("/available", response_model=SlotSearchResponse)
async def search_available_slots(
    sport_id: uuid.UUID,
    search_date: date,
    duration_minutes: Optional[int] = Query(default=None, gt=0, le=720),
    pitch_format: Optional[str] = Query(default=None, max_length=50),
    surface: Optional[str] = Query(default=None, max_length=50),
    db: AsyncSession = Depends(get_db),
) -> SlotSearchResponse:
    return await slot_service.search_available_slots(
        db,
        sport_id=sport_id,
        search_date=search_date,
        duration_minutes=duration_minutes,
        pitch_format=pitch_format,
        surface=surface,
    )
