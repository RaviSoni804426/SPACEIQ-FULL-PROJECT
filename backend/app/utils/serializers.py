from __future__ import annotations

from sqlalchemy import inspect

from app.models import Booking, Space


def serialize_space(space: Space, availability_count: int | None = None) -> dict:
    return {
        "id": space.id,
        "google_place_id": space.google_place_id,
        "name": space.name,
        "type": space.type,
        "description": space.description,
        "address": space.address,
        "city": space.city,
        "locality": space.locality,
        "latitude": space.latitude,
        "longitude": space.longitude,
        "price_per_hour": space.price_per_hour,
        "rating": space.rating,
        "total_reviews": space.total_reviews,
        "amenities": space.amenities or [],
        "images": space.images or [],
        "is_active": space.is_active,
        "website_url": space.website_url,
        "phone_number": space.phone_number,
        "source": space.source,
        "operating_hours": space.operating_hours or {},
        "availability_count": availability_count,
    }


def serialize_booking(booking: Booking) -> dict:
    space = booking.space
    review = None
    if "review" not in inspect(booking).unloaded:
        review = booking.review
    images = space.images if space else []
    return {
        "id": booking.id,
        "user_id": booking.user_id,
        "space_id": booking.space_id,
        "slot_id": booking.slot_id,
        "booking_date": booking.booking_date,
        "start_time": booking.start_time,
        "end_time": booking.end_time,
        "total_amount": booking.total_amount,
        "status": booking.status,
        "razorpay_order_id": booking.razorpay_order_id,
        "razorpay_payment_id": booking.razorpay_payment_id,
        "cancellation_reason": booking.cancellation_reason,
        "created_at": booking.created_at,
        "space_name": space.name if space else "",
        "locality": space.locality if space else None,
        "image_url": images[0] if images else None,
        "review_submitted": review is not None,
        "review_rating": review.rating if review else None,
    }
