from __future__ import annotations

import asyncio

from sqlalchemy import func, select

from app.database import SessionLocal
from app.models import User, UserRole
from app.utils.security import get_password_hash


DEMO_USERS = [
    {
        "email": "test@spacebook.in",
        "full_name": "SpaceBook Test User",
        "phone": "9876543210",
        "role": UserRole.user,
    },
    {
        "email": "partner@spacebook.in",
        "full_name": "SpaceBook Partner",
        "phone": "9876500000",
        "role": UserRole.partner,
    },
]
DEFAULT_PASSWORD = "Test@123"


async def upsert_demo_users() -> None:
    async with SessionLocal() as session:
        for payload in DEMO_USERS:
            result = await session.execute(
                select(User).where(func.lower(User.email) == payload["email"].lower())
            )
            user = result.scalar_one_or_none()
            if user is None:
                user = User(
                    email=payload["email"],
                    hashed_password=get_password_hash(DEFAULT_PASSWORD),
                    full_name=payload["full_name"],
                    phone=payload["phone"],
                    role=payload["role"],
                )
                session.add(user)
                print(f"Created {payload['email']} ({payload['role'].value})")
            else:
                user.full_name = payload["full_name"]
                user.phone = payload["phone"]
                user.role = payload["role"]
                user.hashed_password = get_password_hash(DEFAULT_PASSWORD)
                print(f"Updated {payload['email']} ({payload['role'].value})")

        await session.commit()


if __name__ == "__main__":
    asyncio.run(upsert_demo_users())
