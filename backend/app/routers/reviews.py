from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db
from app.models import Booking, BookingStatus, Review, Space, User
from app.schemas import ReviewCreateRequest, ReviewOut
from app.utils.errors import api_error
from app.utils.security import get_current_user


router = APIRouter(prefix="/api/reviews", tags=["reviews"])


@router.post("", response_model=ReviewOut)
async def create_review(
    payload: ReviewCreateRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> ReviewOut:
    booking_result = await session.execute(
        select(Booking)
        .options(selectinload(Booking.review))
        .where(Booking.id == payload.booking_id, Booking.user_id == user.id)
    )
    booking = booking_result.scalar_one_or_none()
    if not booking:
        raise api_error(404, "Booking not found", "booking_not_found")
    if booking.status not in {BookingStatus.confirmed, BookingStatus.completed}:
        raise api_error(400, "Only confirmed or completed bookings can be reviewed", "invalid_booking_status")
    if booking.review is not None:
        raise api_error(400, "A review already exists for this booking", "review_already_exists")

    review = Review(
        user_id=user.id,
        space_id=booking.space_id,
        booking_id=booking.id,
        rating=payload.rating,
        comment=payload.comment.strip() if payload.comment else None,
    )
    session.add(review)
    await session.flush()

    review_stats = await session.execute(
        select(func.count(Review.id), func.avg(Review.rating)).where(Review.space_id == booking.space_id)
    )
    total_reviews, average_rating = review_stats.one()

    space_result = await session.execute(select(Space).where(Space.id == booking.space_id))
    space = space_result.scalar_one_or_none()
    if not space:
        raise api_error(404, "Space not found", "space_not_found")

    space.total_reviews = int(total_reviews or 0)
    space.rating = round(float(average_rating or 0), 2) if average_rating is not None else None

    await session.commit()
    await session.refresh(review)
    return ReviewOut.model_validate(review)
