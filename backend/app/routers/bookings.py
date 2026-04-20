from __future__ import annotations

from datetime import datetime, timezone
import uuid

from fastapi import APIRouter, Depends
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Booking, BookingStatus, Space, User
from app.schemas import BookingCard, BookingCreateRequest, BookingOut, CancelBookingRequest, HoldRequest, HoldResponse
from app.services.razorpay_service import verify_signature
from app.services.slot_manager import cancel_booking, create_booking_from_hold, hold_slots
from app.utils.errors import api_error
from app.utils.security import get_current_user
from app.utils.serializers import serialize_booking


router = APIRouter(prefix="/api/bookings", tags=["bookings"])


@router.get("/my", response_model=list[BookingCard])
async def my_bookings(
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> list[BookingCard]:
    result = await session.execute(
        select(Booking)
        .options(selectinload(Booking.space), selectinload(Booking.review))
        .where(Booking.user_id == user.id)
        .order_by(desc(Booking.booking_date), desc(Booking.start_time))
    )
    return [BookingCard.model_validate(serialize_booking(booking)) for booking in result.scalars().all()]


@router.post("/hold", response_model=HoldResponse)
async def hold_booking_slots(
    payload: HoldRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> HoldResponse:
    result = await session.execute(select(Space).where(Space.id == payload.space_id, Space.is_active.is_(True)))
    space = result.scalar_one_or_none()
    if not space:
        raise api_error(404, "Space not found", "space_not_found")
    hold = await hold_slots(session, user, space, payload.date, payload.slot_ids)
    return HoldResponse(
        hold_id=hold["hold_id"],
        expires_at=hold["expires_at"],
        total_amount=hold["total_amount"],
        slot_ids=payload.slot_ids,
        booking_date=payload.date,
    )


@router.post("/create", response_model=BookingCard)
async def create_booking(
    payload: BookingCreateRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingCard:
    if not payload.razorpay_order_id or not payload.razorpay_payment_id or not payload.razorpay_signature:
        raise api_error(400, "Verified Razorpay payment details are required", "payment_verification_required")
    verify_signature(payload.razorpay_order_id, payload.razorpay_payment_id, payload.razorpay_signature)
    booking = await create_booking_from_hold(
        session,
        user,
        payload.hold_id,
        payload.razorpay_order_id,
        payload.razorpay_payment_id,
        payload.razorpay_signature,
    )
    await session.refresh(booking, attribute_names=["space"])
    return BookingCard.model_validate(serialize_booking(booking))


@router.get("/{booking_id}", response_model=BookingCard)
async def get_booking(
    booking_id: str,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingCard:
    result = await session.execute(
        select(Booking)
        .options(selectinload(Booking.space), selectinload(Booking.review))
        .where(Booking.id == uuid.UUID(booking_id), Booking.user_id == user.id)
    )
    booking = result.scalar_one_or_none()
    if not booking:
        raise api_error(404, "Booking not found", "booking_not_found")
    return BookingCard.model_validate(serialize_booking(booking))


@router.put("/{booking_id}/cancel", response_model=BookingOut)
async def cancel_user_booking(
    booking_id: str,
    payload: CancelBookingRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingOut:
    result = await session.execute(select(Booking).where(Booking.id == uuid.UUID(booking_id), Booking.user_id == user.id))
    booking = result.scalar_one_or_none()
    if not booking:
        raise api_error(404, "Booking not found", "booking_not_found")
    if booking.status != BookingStatus.confirmed:
        raise api_error(400, "Only confirmed bookings can be cancelled", "invalid_booking_status")

    booking_dt = datetime.combine(booking.booking_date, booking.start_time, tzinfo=timezone.utc)
    if booking_dt <= datetime.now(timezone.utc):
        raise api_error(400, "Past bookings cannot be cancelled", "booking_already_started")

    updated = await cancel_booking(session, booking, payload.reason)
    return BookingOut.model_validate(updated)
