from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List

from auth import get_current_user, require_admin
from config import settings
from database import get_db
import models, schemas
from services.booking_service import (
    booking_conflict_exists,
    approve_pending_booking,
    calculate_booking_price,
    create_confirmed_booking,
    create_pending_booking,
    get_active_unit,
    serialize_booking,
    validate_runtime_booking_window,
)

router = APIRouter(prefix="/bookings", tags=["bookings"])


@router.post("/hold", response_model=schemas.HoldResponse)
def hold_booking(
    req: schemas.HoldRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    validate_runtime_booking_window(req.start_time, req.end_time)
    unit = get_active_unit(req.unit_id, db)

    if booking_conflict_exists(req.unit_id, req.start_time, req.end_time, db):
        raise HTTPException(409, "Slot already booked")

    try:
        from services.redis_service import hold_unit

        slot_key = f"{req.start_time.date()}_{req.start_time.hour}"
        hold_unit(req.unit_id, slot_key, user.id)
    except HTTPException:
        raise
    except Exception:
        pass

    price = calculate_booking_price(unit, req.start_time, db)

    razorpay_order_id = f"order_demo_{user.id[:8]}"
    if settings.real_payments_enabled:
        try:
            import razorpay

            rzp = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
            order = rzp.order.create({"amount": int(price * 100), "currency": "INR"})
            razorpay_order_id = order["id"]
        except Exception:
            pass

    return {
        "held": True,
        "price": price,
        "razorpay_order_id": razorpay_order_id,
        "expires_in_seconds": 300,
    }


@router.post("/confirm")
def confirm_booking(
    req: schemas.ConfirmRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    unit = get_active_unit(req.unit_id, db)
    if settings.booking_mode.strip().lower() == "request":
        booking = create_pending_booking(
            user=user,
            unit=unit,
            start_time=req.start_time,
            end_time=req.end_time,
            amount=req.amount,
            source=req.source,
            order_id=req.order_id,
            payment_id=req.payment_id,
            db=db,
        )

        try:
            from services.redis_service import release_hold

            slot_key = f"{req.start_time.date()}_{req.start_time.hour}"
            release_hold(req.unit_id, slot_key)
        except Exception:
            pass

        return {
            "booking_id": booking.id,
            "status": "pending",
            "detail": "Booking request submitted. Venue confirmation is required before payment capture.",
            "qr_token": None,
            "qr_image_b64": None,
        }

    if settings.real_payments_enabled:
        if not req.order_id or not req.payment_id or not req.signature:
            raise HTTPException(400, "order_id, payment_id, and signature are required when real payments are enabled.")
        try:
            import razorpay

            rzp = razorpay.Client(auth=(settings.razorpay_key_id, settings.razorpay_key_secret))
            rzp.utility.verify_payment_signature(
                {
                    "razorpay_order_id": req.order_id,
                    "razorpay_payment_id": req.payment_id,
                    "razorpay_signature": req.signature,
                }
            )
        except Exception as exc:
            raise HTTPException(400, "Payment signature verification failed") from exc

    booking, token, qr_image = create_confirmed_booking(
        user=user,
        unit=unit,
        start_time=req.start_time,
        end_time=req.end_time,
        amount=req.amount,
        source=req.source,
        order_id=req.order_id or f"order_demo_{user.id[:8]}",
        payment_id=req.payment_id or f"pay_demo_{unit.id[:6]}",
        db=db,
    )

    try:
        from services.redis_service import release_hold

        slot_key = f"{req.start_time.date()}_{req.start_time.hour}"
        release_hold(req.unit_id, slot_key)
    except Exception:
        pass

    return {"booking_id": booking.id, "status": "confirmed", "detail": "Booking confirmed.", "qr_token": token, "qr_image_b64": qr_image}


@router.get("/my", response_model=List[schemas.BookingOut])
def my_bookings(
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Booking)
        .filter(models.Booking.user_id == user.id)
        .order_by(models.Booking.created_at.desc())
        .all()
    )
    return [serialize_booking(booking) for booking in rows]


@router.delete("/{booking_id}")
def cancel_booking(
    booking_id: str,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    booking = (
        db.query(models.Booking)
        .filter(
            models.Booking.id == booking_id,
            models.Booking.user_id == user.id,
        )
        .first()
    )
    if not booking:
        raise HTTPException(404, "Booking not found")
    if booking.status in (models.BookingStatus.confirmed, models.BookingStatus.pending):
        booking.status = models.BookingStatus.cancelled
        db.commit()
    return {"cancelled": True, "booking_id": booking_id}


@router.get("/requests", response_model=List[schemas.BookingOut])
def list_pending_booking_requests(
    _admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(models.Booking)
        .filter(models.Booking.status == models.BookingStatus.pending)
        .order_by(models.Booking.created_at.desc())
        .limit(100)
        .all()
    )
    return [serialize_booking(booking) for booking in rows]


@router.post("/requests/{booking_id}/review")
def review_booking_request(
    booking_id: str,
    req: schemas.BookingReviewRequest,
    _admin: models.User = Depends(require_admin),
    db: Session = Depends(get_db),
):
    booking = db.query(models.Booking).filter(models.Booking.id == booking_id).first()
    if not booking:
        raise HTTPException(404, "Booking request not found")

    action = req.action.strip().lower()
    if action not in {"approve", "reject"}:
        raise HTTPException(400, "Action must be approve or reject")

    if action == "reject":
        booking.status = models.BookingStatus.cancelled
        if booking.payment:
            booking.payment.status = "failed"
        db.commit()
        return {"reviewed": True, "booking_id": booking.id, "status": "cancelled", "detail": "Booking request rejected."}

    approved, token, qr_image = approve_pending_booking(booking, db)
    return {
        "reviewed": True,
        "booking_id": approved.id,
        "status": "confirmed",
        "detail": "Booking request approved and confirmed.",
        "qr_token": token,
        "qr_image_b64": qr_image,
    }


