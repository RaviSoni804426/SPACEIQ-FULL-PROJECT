from __future__ import annotations

import asyncio

from app.database import SessionLocal
from app.services.demo_inventory import upsert_demo_inventory


async def seed_demo_inventory() -> None:
    async with SessionLocal() as session:
        result = await upsert_demo_inventory(session)
        print(result["detail"])
        print(f"Seeded {result['synced']} demo spaces.")


if __name__ == "__main__":
    asyncio.run(seed_demo_inventory())
