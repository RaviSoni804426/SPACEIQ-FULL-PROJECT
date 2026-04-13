from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SearchEvent, Space, User
from app.schemas import RecentSearchOut, TrendingLocalityOut
from app.utils.security import get_current_user


router = APIRouter(prefix="/api/discovery", tags=["discovery"])


@router.get("/recent-searches", response_model=list[RecentSearchOut])
async def recent_searches(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[RecentSearchOut]:
    result = await session.execute(
        select(SearchEvent)
        .where(SearchEvent.user_id == user.id)
        .order_by(desc(SearchEvent.created_at))
        .limit(10)
    )
    deduped: list[RecentSearchOut] = []
    seen: set[tuple[str, str | None]] = set()
    for event in result.scalars().all():
        key = (event.query.strip().lower(), event.locality.strip().lower() if event.locality else None)
        if key in seen:
            continue
        seen.add(key)
        deduped.append(
            RecentSearchOut(
                query=event.query,
                locality=event.locality,
                created_at=event.created_at,
            )
        )
        if len(deduped) >= 5:
            break
    return deduped


@router.get("/trending-localities", response_model=list[TrendingLocalityOut])
async def trending_localities(session: AsyncSession = Depends(get_db)) -> list[TrendingLocalityOut]:
    result = await session.execute(
        select(
            Space.locality,
            func.count(Space.id).label("space_count"),
            func.avg(Space.price_per_hour).label("average_price"),
        )
        .where(Space.is_active.is_(True), Space.locality.is_not(None))
        .group_by(Space.locality)
        .order_by(desc(func.count(Space.id)), desc(func.avg(Space.rating)))
        .limit(6)
    )
    return [
        TrendingLocalityOut(
            locality=str(row[0]),
            space_count=int(row[1] or 0),
            average_price=float(row[2] or 0),
        )
        for row in result.all()
    ]
