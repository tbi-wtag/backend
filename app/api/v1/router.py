from fastapi import APIRouter

from app.api.v1.auth import router as auth_router
from app.api.v1.users import router as users_router
from app.api.v1.sports import router as sports_router
from app.api.v1.admin_resources import router as admin_resources_router
from app.api.v1.admin_opening_hours import router as admin_opening_hours_router
from app.api.v1.admin_time_blocks import router as admin_time_blocks_router
from app.api.v1.slots import router as slots_router
from app.api.v1.pricing import router as pricing_router

api_v1_router = APIRouter()

api_v1_router.include_router(auth_router, tags=["Authentication"])
api_v1_router.include_router(users_router, tags=["Users"])
api_v1_router.include_router(sports_router, tags=["Sports"])
api_v1_router.include_router(slots_router)
api_v1_router.include_router(pricing_router)
api_v1_router.include_router(
    admin_resources_router, prefix="/admin", tags=["Admin - Resources"]
)
api_v1_router.include_router(
    admin_opening_hours_router, prefix="/admin", tags=["Admin - Opening Hours"]
)
api_v1_router.include_router(
    admin_time_blocks_router, prefix="/admin", tags=["Admin - Time Blocks"]
)
