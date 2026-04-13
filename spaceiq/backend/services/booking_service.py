from __future__ import annotations

from datetime import datetime, timedelta
from typing import Optional

from fastapi import HTTPException
from sqlalchemy.orm import Session

import models
from services.ml.pricing import get_dynamic_price
from services.qr_service import generate_qr_image_b64, generate_qr_token


ACTIVE_BOOKING_STATUSES = (
    models.BookingStatus.pending,
    models.BookingStatus.confirmed,
)


def validate_runtime_booking_window(start_time: datetime, end_time: datetime) -> None:
    if end_time <= start_time:
        raise HTTPException(400, "End time must be after start time.")
    if start_time < datetime.utcnow():
        raise HTTPException(400, "Bookings must be created for a future time slot.")


def get_active_unit(unit_id: str, db: Session) -> models.Unit:
    unit = (
        db.query(models.Unit)
        .filter(models.Unit.id == unit_id, models.Unit.is_active == True)
        .first()
    )
    if not unit:
        raise HTTPException(404, "Unit not found")
    return unit


def booking_conflict_exists(
    unit_id: str,
    start_time: datetime,
    end_time: datetime,
    db: Session,
    exclude_booking_id: str | None = None,
) -> bool:
    q = (
        db.query(models.Booking.id)
        .filter(
            models.Booking.unit_id == unit_id,
            models.Booking.start_time < end_time,
            models.Booking.end_time > start_time,
            models.Booking.status.in_(ACTIVE_BOOKING_STATUSES),
        )
    )
    if exclude_booking_id:
        q = q.filter(models.Booking.id != exclude_booking_id)
    return q.first() is not None


def estimate_unit_occupancy(unit_id: str, when: datetime, db: Session) -> float:
    day_start = when.replace(hour=0, minute=0, second=0, microsecond=0)
    day_end = day_start + timedelta(days=1)
    count = (
        db.query(models.Booking)
        .filter(
            models.Booking.unit_id == unit_id,
            models.Booking.start_time >= day_start,
            models.Booking.start_time < day_end,
            models.Booking.status.in_(ACTIVE_BOOKING_STATUSES),
        )
        .count()
    )
    return min(count / 10.0, 1.0)


def calculate_booking_price(unit: models.Unit, start_time: datetime, db: Session) -> float:
    occupancy = estimate_unit_occupancy(unit.id, start_time, db)
    return get_dynamic_price(unit.base_price, start_time, occupancy)


def serialize_booking(booking: models.Booking) -> dict:
    return {
        "id": booking.id,
        "unit_id": booking.unit_id,
        "unit_name": booking.unit.name if booking.unit else None,
        "location_name": booking.unit.location.name if booking.unit and booking.unit.location else None,
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "total_amount": booking.total_amount,
        "status": str(booking.status.value if hasattr(booking.status, "value") else booking.status),
        "source": booking.source,
        "qr_token": booking.qr_code.token if booking.qr_code else None,
        "created_at": booking.created_at,
    }


def create_confirmed_booking(
    *,
    user: models.User,
    unit: models.Unit,
    start_time: datetime,
    end_time: datetime,
    amount: float,
    source: str,
    order_id: str,
    payment_id: str,
    db: Session,
) -> tuple[models.Booking, str, str]:
    validate_runtime_booking_window(start_time, end_time)
    if booking_conflict_exists(unit.id, start_time, end_time, db):
        raise HTTPException(409, "Slot already booked")
    if amount <= 0:
        raise HTTPException(400, "Booking amount must be greater than zero.")

    booking = models.Booking(
        user_id=user.id,
        unit_id=unit.id,
        start_time=start_time,
        end_time=end_time,
        total_amount=round(float(amount), 2),
        status=models.BookingStatus.confirmed,
        source=source,
    )
    db.add(booking)
    db.flush()

    db.add(
        models.Payment(
            booking_id=booking.id,
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            amount=booking.total_amount,
            status="success",
        )
    )

    token = generate_qr_token(booking.id)
    db.add(
        models.QRCode(
            booking_id=booking.id,
            token=token,
            expires_at=end_time + timedelta(minutes=15),
        )
    )

    user.loyalty_pts = (user.loyalty_pts or 0) + int(booking.total_amount / 10)
    db.commit()
    db.refresh(booking)
    return booking, token, generate_qr_image_b64(token)


def create_pending_booking(
    *,
    user: models.User,
    unit: models.Unit,
    start_time: datetime,
    end_time: datetime,
    amount: float,
    source: str,
    order_id: Optional[str],
    payment_id: Optional[str],
    db: Session,
) -> models.Booking:
    validate_runtime_booking_window(start_time, end_time)
    if booking_conflict_exists(unit.id, start_time, end_time, db):
        raise HTTPException(409, "Slot already booked")
    if amount <= 0:
        raise HTTPException(400, "Booking amount must be greater than zero.")

    booking = models.Booking(
        user_id=user.id,
        unit_id=unit.id,
        start_time=start_time,
        end_time=end_time,
        total_amount=round(float(amount), 2),
        status=models.BookingStatus.pending,
        source=source,
    )
    db.add(booking)
    db.flush()

    db.add(
        models.Payment(
            booking_id=booking.id,
            razorpay_order_id=order_id,
            razorpay_payment_id=payment_id,
            amount=booking.total_amount,
            status="pending",
        )
    )

    db.commit()
    db.refresh(booking)
    return booking


def approve_pending_booking(booking: models.Booking, db: Session) -> tuple[models.Booking, str, str]:
    if str(booking.status.value if hasattr(booking.status, "value") else booking.status) != models.BookingStatus.pending.value:
        raise HTTPException(400, "Only pending booking requests can be approved.")

    if booking_conflict_exists(booking.unit_id, booking.start_time, booking.end_time, db, exclude_booking_id=booking.id):
        raise HTTPException(409, "Cannot approve request because the slot is no longer available.")

    booking.status = models.BookingStatus.confirmed

    payment = booking.payment
    if payment:
        payment.status = "success"

    token = generate_qr_token(booking.id)
    db.add(
        models.QRCode(
            booking_id=booking.id,
            token=token,
            expires_at=booking.end_time + timedelta(minutes=15),
        )
    )

    if booking.user:
        booking.user.loyalty_pts = (booking.user.loyalty_pts or 0) + int(booking.total_amount / 10)

    db.commit()
    db.refresh(booking)
    return booking, token, generate_qr_image_b64(token)
