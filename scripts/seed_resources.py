import asyncio
from decimal import Decimal
from sqlalchemy import select

from app.db.session import AsyncSessionLocal
from app.models.resource import Resource
from app.models.sport import Sport

INITIAL_RESOURCES = [
    {
        "resource_name": "Pitch 1",
        "pitch_format": "5-a-side",
        "surface": "Artificial Turf",
        "capacity": 10,
        "price_per_hour": Decimal("500.00"),
        "is_active": True,
        "sport_name": "Football",
    },
]


async def seed_resources() -> None:
    async with AsyncSessionLocal() as db:
        for resource_data in INITIAL_RESOURCES:

            result = await db.execute(
                select(Sport).where(Sport.sport_name == resource_data["sport_name"])
            )
            sport = result.scalars().first()

            if not sport:
                print(f"Sport '{resource_data['sport_name']}' does not exist.")
                continue

            result = await db.execute(
                select(Resource).where(
                    (Resource.resource_name == resource_data["resource_name"])
                    & (Resource.sport_id == sport.id)
                )
            )
            existing_resource = result.scalars().first()

            if existing_resource:
                print(
                    f"Resource '{resource_data['resource_name']}' already exists for sport '{resource_data['sport_name']}'."
                )
                continue

            new_resource = Resource(
                resource_name=resource_data["resource_name"],
                pitch_format=resource_data["pitch_format"],
                surface=resource_data["surface"],
                capacity=resource_data["capacity"],
                price_per_hour=resource_data["price_per_hour"],
                is_active=resource_data["is_active"],
                sport_id=sport.id,
            )

            db.add(new_resource)
            print(
                f"Created resource: {resource_data['resource_name']} for sport: {resource_data['sport_name']}"
            )

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_resources())
