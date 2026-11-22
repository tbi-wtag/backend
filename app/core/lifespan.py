import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.services.booking_helpers import sync_booking_statuses

logger = logging.getLogger(__name__)


async def _booking_status_worker() -> None:
    while True:
        try:
            async with AsyncSessionLocal() as db:
                expired, completed = await sync_booking_statuses(db)
                if expired or completed:
                    logger.info(
                        "Booking status sync: %d expired, %d completed",
                        expired,
                        completed,
                    )
        except asyncio.CancelledError:
            break
        except Exception:
            logger.exception("Error during automatic booking status sync")

        await asyncio.sleep(settings.booking.status_sync_interval_seconds)


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(_booking_status_worker())
    try:
        yield
    finally:
        task.cancel()
        await asyncio.gather(task, return_exceptions=True)
