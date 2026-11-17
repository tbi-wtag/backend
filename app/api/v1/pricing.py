from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.dependencies import get_db
from app.core.rate_limiter import limiter
from app.schemas.pricing import PriceQuoteRequest, PriceQuoteResponse
from app.services import pricing_service

router = APIRouter(prefix="/pricing", tags=["Pricing"])


@router.post("/quote", response_model=PriceQuoteResponse)
@limiter.limit("10/minute")
async def create_price_quote(
    request: Request,
    response: Response,
    quote_in: PriceQuoteRequest,
    db: AsyncSession = Depends(get_db),
) -> PriceQuoteResponse:
    return await pricing_service.generate_price_quote(db=db, quote_in=quote_in)
