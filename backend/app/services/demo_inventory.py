from __future__ import annotations

from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Space, SpaceType, User, UserRole


DEMO_SOURCE = "demo_seed"


def _hours(open_at: str, close_at: str) -> dict[str, list[str]]:
    return {
        "mon": [open_at, close_at],
        "tue": [open_at, close_at],
        "wed": [open_at, close_at],
        "thu": [open_at, close_at],
        "fri": [open_at, close_at],
        "sat": [open_at, close_at],
        "sun": [open_at, close_at],
    }


DEMO_SPACES: list[dict[str, object]] = [
    {
        "name": "Indiranagar Workdeck",
        "type": SpaceType.coworking,
        "description": "Bright coworking desks with meeting pods and fast WiFi near the metro.",
        "address": "100 Feet Road, Indiranagar, Bangalore",
        "city": "Bangalore",
        "locality": "Indiranagar",
        "latitude": 12.9784,
        "longitude": 77.6408,
        "price_per_hour": Decimal("499.00"),
        "rating": 4.6,
        "total_reviews": 128,
        "amenities": ["WiFi", "AC", "Parking", "Cafeteria", "Projector"],
        "images": [
            "https://images.unsplash.com/photo-1497366754035-f200968a6e72?auto=format&fit=crop&w=1200&q=80"
        ],
        "operating_hours": _hours("08:00", "21:00"),
    },
    {
        "name": "Koramangala Huddle Rooms",
        "type": SpaceType.meeting_room,
        "description": "Premium meeting suites for quick team syncs, client calls, and hybrid interviews.",
        "address": "80 Feet Road, Koramangala, Bangalore",
        "city": "Bangalore",
        "locality": "Koramangala",
        "latitude": 12.9352,
        "longitude": 77.6245,
        "price_per_hour": Decimal("1199.00"),
        "rating": 4.7,
        "total_reviews": 84,
        "amenities": ["WiFi", "AC", "Parking", "Projector"],
        "images": [
            "https://images.unsplash.com/photo-1497366412874-3415097a27e7?auto=format&fit=crop&w=1200&q=80"
        ],
        "operating_hours": _hours("08:00", "20:00"),
    },
    {
        "name": "HSR Creator Studio",
        "type": SpaceType.studio,
        "description": "Flexible studio rental for creators, podcasts, shoots, and small production teams.",
        "address": "27th Main Road, HSR Layout, Bangalore",
        "city": "Bangalore",
        "locality": "HSR Layout",
        "latitude": 12.9116,
        "longitude": 77.6474,
        "price_per_hour": Decimal("1499.00"),
        "rating": 4.5,
        "total_reviews": 41,
        "amenities": ["AC", "Parking", "Soundproofing", "Power Backup"],
        "images": [
            "https://images.unsplash.com/photo-1516280440614-37939bbacd81?auto=format&fit=crop&w=1200&q=80"
        ],
        "operating_hours": _hours("09:00", "21:00"),
    },
    {
        "name": "Whitefield Rally Arena",
        "type": SpaceType.sports,
        "description": "Floodlit turf and multi-sport court slots for after-work games and weekend leagues.",
        "address": "ITPL Main Road, Whitefield, Bangalore",
        "city": "Bangalore",
        "locality": "Whitefield",
        "latitude": 12.9698,
        "longitude": 77.7499,
        "price_per_hour": Decimal("999.00"),
        "rating": 4.4,
        "total_reviews": 93,
        "amenities": ["Parking", "Washroom", "Floodlights", "AC"],
        "images": [
            "https://images.unsplash.com/photo-1517649763962-0c623066013b?auto=format&fit=crop&w=1200&q=80"
        ],
        "operating_hours": _hours("06:00", "22:00"),
    },
    {
        "name": "Jayanagar Focus Hub",
        "type": SpaceType.coworking,
        "description": "Quiet neighborhood workspace with day passes, meeting booths, and backup power.",
        "address": "11th Main, Jayanagar, Bangalore",
        "city": "Bangalore",
        "locality": "Jayanagar",
        "latitude": 12.9279,
        "longitude": 77.5837,
        "price_per_hour": Decimal("449.00"),
        "rating": 4.3,
        "total_reviews": 57,
        "amenities": ["WiFi", "AC", "Parking", "Power Backup"],
        "images": [
            "https://images.unsplash.com/photo-1524758631624-e2822e304c36?auto=format&fit=crop&w=1200&q=80"
        ],
        "operating_hours": _hours("08:00", "20:00"),
    },
    {
        "name": "Bellandur Sprint Courts",
        "type": SpaceType.sports,
        "description": "Bookable badminton and box-cricket slots with changing rooms and parking.",
        "address": "Outer Ring Road, Bellandur, Bangalore",
        "city": "Bangalore",
        "locality": "Bellandur",
        "latitude": 12.9304,
        "longitude": 77.6784,
        "price_per_hour": Decimal("899.00"),
        "rating": 4.2,
        "total_reviews": 76,
        "amenities": ["Parking", "Washroom", "Floodlights"],
        "images": [
            "https://images.unsplash.com/photo-1547347298-4074fc3086f0?auto=format&fit=crop&w=1200&q=80"
        ],
        "operating_hours": _hours("06:00", "22:00"),
    },
]


async def upsert_demo_inventory(session: AsyncSession) -> dict[str, object]:
    partner_result = await session.execute(
        select(User).where(User.role == UserRole.partner).order_by(User.created_at.asc())
    )
    partner = partner_result.scalars().first()

    synced = 0
    for payload in DEMO_SPACES:
        result = await session.execute(
            select(Space).where(
                Space.name == payload["name"],
                Space.address == payload["address"],
                Space.source == DEMO_SOURCE,
            )
        )
        space = result.scalar_one_or_none()
        if space is None:
            space = Space(name=str(payload["name"]), type=payload["type"])
            session.add(space)

        for field, value in payload.items():
            setattr(space, field, value)
        space.owner_id = partner.id if partner else None
        space.source = DEMO_SOURCE
        space.is_active = True
        synced += 1

    await session.commit()
    return {
        "synced": synced,
        "source": DEMO_SOURCE,
        "detail": "Demo Bangalore inventory seeded for local development.",
    }
