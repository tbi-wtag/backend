import asyncio
from sqlalchemy import select
from app.db.session import AsyncSessionLocal
from app.models.sport import Sport

INITIAL_SPORTS = [
    {
        "sport_name": "Football",
        "min_hours": 1,
        "max_hours": 3,
        "is_active": True,
    },
]


async def seed_sports() -> None:
    async with AsyncSessionLocal() as db:
        for sport_data in INITIAL_SPORTS:
            result = await db.execute(
                select(Sport).where(Sport.sport_name == sport_data["sport_name"])
            )
            existing_sport = result.scalars().first()

            if existing_sport:
                print(f"Sport '{sport_data['sport_name']}' already exists.")
                continue

            new_sport = Sport(
                sport_name=sport_data["sport_name"],
                min_hours=sport_data["min_hours"],
                max_hours=sport_data["max_hours"],
                is_active=sport_data["is_active"],
            )

            db.add(new_sport)
            print(f"Created sport: {sport_data['sport_name']}")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_sports())
