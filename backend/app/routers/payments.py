from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import Booking, User
from app.schemas import BookingCard, PaymentInitRequest, PaymentInitResponse, PaymentVerifyRequest
from app.services.razorpay_service import create_order, verify_signature
from app.services.slot_manager import create_booking_from_hold, get_hold_context
from app.utils.rate_limit import limiter
from app.utils.security import get_current_user
from app.utils.serializers import serialize_booking


router = APIRouter(prefix="/api/payments", tags=["payments"])


@router.post("/init", response_model=PaymentInitResponse)
@limiter.limit(settings.payment_rate_limit)
async def init_payment(
    request: Request,
    payload_data: dict = Body(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> PaymentInitResponse:
    payload = PaymentInitRequest.model_validate(payload_data)
    slots, space = await get_hold_context(session, payload.hold_id, user.id)
    amount = float(space.price_per_hour) * len(slots)
    order = await create_order(
        amount_rupees=amount,
        receipt=f"hold-{payload.hold_id}",
        notes={"space_id": str(space.id), "user_id": str(user.id)},
    )
    return PaymentInitResponse(
        order_id=order["id"],
        key_id=settings.next_public_razorpay_key_id or settings.razorpay_key_id or "demo_key",
        amount=order["amount"],
        hold_id=payload.hold_id,
        mode=order.get("mode", "razorpay"),
        booking_summary={
            "space_name": space.name,
            "locality": space.locality or "Bangalore",
            "date": slots[0].date.isoformat(),
            "start_time": slots[0].start_time.strftime("%H:%M"),
            "end_time": slots[-1].end_time.strftime("%H:%M"),
            "total_amount": amount,
        },
    )


@router.post("/verify", response_model=BookingCard)
@limiter.limit(settings.payment_rate_limit)
async def verify_payment(
    request: Request,
    payload_data: dict = Body(...),
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> BookingCard:
    payload = PaymentVerifyRequest.model_validate(payload_data)
    existing_result = await session.execute(
        select(Booking)
        .options(selectinload(Booking.space), selectinload(Booking.review))
        .where(Booking.razorpay_payment_id == payload.razorpay_payment_id)
    )
    existing = existing_result.scalar_one_or_none()
    if existing:
        return BookingCard.model_validate(serialize_booking(existing))

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
