from decimal import Decimal
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.resource import Resource
from app.schemas.pricing import PriceQuoteRequest, PriceQuoteResponse
from app.services import slot_service


def calculate_total_price(resources: list[Resource], duration_minutes: int) -> Decimal:
    hours = Decimal(duration_minutes) / 60
    total = sum((r.price_per_hour * hours for r in resources), Decimal("0.00"))
    return total.quantize(Decimal("0.01"))


async def generate_price_quote(
    db: AsyncSession,
    *,
    quote_in: PriceQuoteRequest,
) -> PriceQuoteResponse:
    allocated, slot_start_time, slot_end_time = (
        await slot_service.resolve_and_validate_resources(
            db,
            sport_id=quote_in.sport_id,
            start_at=quote_in.start_at,
            duration_minutes=quote_in.duration_minutes,
            number_of_people=quote_in.number_of_people,
            resource_ids=quote_in.resource_ids,
            pitch_format=quote_in.pitch_format,
            surface=quote_in.surface,
        )
    )

    return PriceQuoteResponse(
        sport_id=quote_in.sport_id,
        start_at=slot_start_time,
        end_at=slot_end_time,
        duration_minutes=quote_in.duration_minutes,
        number_of_people=quote_in.number_of_people,
        resource_ids=[r.id for r in allocated],
        total_price=calculate_total_price(allocated, quote_in.duration_minutes),
    )