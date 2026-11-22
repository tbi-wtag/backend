from typing import Optional
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.resource import crud_resource
from app.models.sport import Sport

MAX_RESOURCES_BY_SPORT = {
    "football": 3,
    "badminton": 4,
    "tennis": 3,
    "volleyball": 2,
    "swimming": 4,
}

FOOTBALL_CAPACITY_BY_FORMAT = {
    "5-a-side": 12,
    "7-a-side": 16,
    "11-a-side": 24,
}

MAX_CAPACITY_BY_SPORT = {
    "badminton": 6,
    "tennis": 6,
    "volleyball": 14,
    "swimming": 4,
}


def validate_sport_specific_rules(
    sport_name: str,
    pitch_format: Optional[str],
    surface: Optional[str],
    capacity: int,
) -> None:
    normalized_sport = sport_name.strip().lower()

    if normalized_sport == "football":
        if not pitch_format:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="pitch_format is required for Football resources (5-a-side, 7-a-side, or 11-a-side).",
            )
        if surface:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="surface is not applicable to Football resources.",
            )
        max_cap = FOOTBALL_CAPACITY_BY_FORMAT[pitch_format]
        if capacity > max_cap:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Capacity for a {pitch_format} pitch cannot exceed {max_cap}.",
            )
        return

    if normalized_sport == "tennis":
        if not surface:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="surface is required for Tennis resources (hard, clay, or grass).",
            )
        if pitch_format:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="pitch_format is not applicable to Tennis resources.",
            )
    else:
        if pitch_format:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="pitch_format is only applicable to Football resources.",
            )
        if surface:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="surface is only applicable to Tennis resources.",
            )

    if normalized_sport in MAX_CAPACITY_BY_SPORT:
        max_cap = MAX_CAPACITY_BY_SPORT[normalized_sport]
        if capacity > max_cap:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Capacity for {sport_name} cannot exceed {max_cap}.",
            )


async def ensure_under_resource_limit(db: AsyncSession, sport: Sport) -> None:
    normalized_sport = sport.sport_name.strip().lower()
    if normalized_sport in MAX_RESOURCES_BY_SPORT:
        max_allowed = MAX_RESOURCES_BY_SPORT[normalized_sport]
        current_count = await crud_resource.count_by_sport(
            db, sport_id=sport.id, is_active=True
        )
        if current_count >= max_allowed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"{sport.sport_name} cannot have more than {max_allowed} active resources.",
            )


async def ensure_unique_name(
    db: AsyncSession, sport: Sport, resource_name: str
) -> None:
    existing = await crud_resource.get_by_sport_and_name(
        db, sport_id=sport.id, resource_name=resource_name
    )
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Resource '{resource_name}' already exists for {sport.sport_name}.",
        )
