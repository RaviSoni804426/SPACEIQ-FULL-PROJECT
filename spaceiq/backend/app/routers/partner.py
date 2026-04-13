from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Booking, Space, User, UserRole
from app.schemas import BookingCard, SpaceSummary
from app.utils.security import require_roles
from app.utils.serializers import serialize_booking, serialize_space


router = APIRouter(prefix="/api/partner", tags=["partner"])


@router.get("/spaces", response_model=list[SpaceSummary])
async def partner_spaces(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.partner, UserRole.admin)),
) -> list[SpaceSummary]:
    query = select(Space).where(Space.is_active.is_(True))
    if user.role == UserRole.partner:
        query = query.where(Space.owner_id == user.id)
    result = await session.execute(query.order_by(desc(Space.created_at)))
    return [SpaceSummary.model_validate(serialize_space(space)) for space in result.scalars().all()]


@router.get("/bookings", response_model=list[BookingCard])
async def partner_bookings(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles(UserRole.partner, UserRole.admin)),
) -> list[BookingCard]:
    query = select(Booking).options(selectinload(Booking.space)).join(Space, Space.id == Booking.space_id)
    if user.role == UserRole.partner:
        query = query.where(Space.owner_id == user.id)
    result = await session.execute(query.order_by(desc(Booking.created_at)))
    return [BookingCard.model_validate(serialize_booking(booking)) for booking in result.scalars().all()]
