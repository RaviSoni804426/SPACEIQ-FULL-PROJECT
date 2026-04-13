from __future__ import annotations

from datetime import date, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Booking, BookingStatus, Review, Space, User, UserRole
from app.schemas import ChartPoint, OverviewStats, RevenueBySpacePoint
from app.utils.security import require_roles


router = APIRouter(prefix="/api/analytics", tags=["analytics"])


def _scope_space_ids_query(user: User):
    if user.role == UserRole.admin:
        return None
    return select(Space.id).where(Space.owner_id == user.id)


@router.get("/overview", response_model=OverviewStats)
async def analytics_overview(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.partner, UserRole.admin)),
) -> OverviewStats:
    space_scope = _scope_space_ids_query(user)
    booking_query = select(Booking).where(Booking.status == BookingStatus.confirmed)
    spaces_query = select(func.count(Space.id)).where(Space.is_active.is_(True))
    reviews_query = select(func.avg(Review.rating))

    if space_scope is not None:
        booking_query = booking_query.where(Booking.space_id.in_(space_scope))
        spaces_query = spaces_query.where(Space.owner_id == user.id)
        reviews_query = reviews_query.where(Review.space_id.in_(space_scope))

    bookings_result = await session.execute(select(func.count()).select_from(booking_query.subquery()))
    revenue_result = await session.execute(select(func.sum(Booking.total_amount)).where(Booking.status == BookingStatus.confirmed))
    if space_scope is not None:
        revenue_result = await session.execute(
            select(func.sum(Booking.total_amount)).where(
                Booking.status == BookingStatus.confirmed,
                Booking.space_id.in_(space_scope),
            )
        )
    spaces_result = await session.execute(spaces_query)
    reviews_result = await session.execute(reviews_query)

    return OverviewStats(
        total_bookings=int(bookings_result.scalar() or 0),
        total_revenue=float(revenue_result.scalar() or 0),
        active_spaces=int(spaces_result.scalar() or 0),
        average_rating=round(float(reviews_result.scalar() or 0), 2),
    )


@router.get("/bookings-by-day", response_model=list[ChartPoint])
async def bookings_by_day(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.partner, UserRole.admin)),
) -> list[ChartPoint]:
    space_scope = _scope_space_ids_query(user)
    start_date = date.today() - timedelta(days=29)
    query = (
        select(Booking.booking_date, func.count(Booking.id))
        .where(Booking.booking_date >= start_date, Booking.status == BookingStatus.confirmed)
        .group_by(Booking.booking_date)
        .order_by(Booking.booking_date)
    )
    if space_scope is not None:
        query = query.where(Booking.space_id.in_(space_scope))
    result = await session.execute(query)
    return [ChartPoint(label=row[0].isoformat(), value=float(row[1])) for row in result.all()]


@router.get("/revenue-by-space", response_model=list[RevenueBySpacePoint])
async def revenue_by_space(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.partner, UserRole.admin)),
) -> list[RevenueBySpacePoint]:
    space_scope = _scope_space_ids_query(user)
    query = (
        select(Space.name, Space.type, func.sum(Booking.total_amount).label("revenue"))
        .join(Booking, Booking.space_id == Space.id)
        .where(Booking.status == BookingStatus.confirmed)
        .group_by(Space.name, Space.type)
        .order_by(func.sum(Booking.total_amount).desc())
        .limit(10)
    )
    if space_scope is not None:
        query = query.where(Space.id.in_(space_scope))
    result = await session.execute(query)
    return [RevenueBySpacePoint(space_name=row[0], space_type=row[1], value=float(row[2] or 0)) for row in result.all()]
