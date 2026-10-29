import asyncio
from sqlalchemy import select, or_

from app.db.session import AsyncSessionLocal
from app.core.security import hash_password
from app.models.user import User

INITIAL_USER = [
    {
        "username": "tejalb29",
        "first_name": "Tejal",
        "last_name": "Bissessur",
        "email": "tejal@gmail.com",
        "password": "abc123456",
        "role": "admin",
        "is_active": True,
    },
    {
        "username": "john12",
        "first_name": "John",
        "last_name": "Doe",
        "email": "john@gmail.com",
        "password": "abc123456",
        "role": "user",
        "is_active": True,
    },
]


async def seed_users() -> None:
    async with AsyncSessionLocal() as db:

        for user_data in INITIAL_USER:
            result = await db.execute(
                select(User).where(
                    (User.username == user_data["username"])
                    | (User.email == user_data["email"])
                )
            )
            existing_user = result.scalars().first()

            if existing_user:
                print(f" User '{user_data['username']}' already exists.")
                continue

            new_user = User(
                username=user_data["username"],
                first_name=user_data["first_name"],
                last_name=user_data["last_name"],
                email=user_data["email"],
                hashed_password=hash_password(user_data["password"]),
                role=user_data["role"],
                is_active=user_data["is_active"],
            )

            db.add(new_user)
            print(f"Created user: {user_data['username']}")

        await db.commit()


if __name__ == "__main__":
    asyncio.run(seed_users())
