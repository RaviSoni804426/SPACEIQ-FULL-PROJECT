from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from database import get_db
from auth import get_current_user
import models, schemas
from services.sentiment import analyze

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.post("/", response_model=schemas.ReviewOut)
def submit_review(
    req: schemas.ReviewRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify user has a completed booking for this unit
    booking = db.query(models.Booking).filter(
        models.Booking.user_id == user.id,
        models.Booking.unit_id == req.unit_id,
        models.Booking.status.in_(["confirmed", "completed"]),
    ).first()
    if not booking:
        raise HTTPException(403, "You can only review spaces you have booked")

    existing_review = (
        db.query(models.Review)
        .filter(models.Review.user_id == user.id, models.Review.unit_id == req.unit_id)
        .first()
    )
    if existing_review:
        raise HTTPException(409, "You have already reviewed this space")

    sentiment = {}
    if req.comment:
        sentiment = analyze(req.comment)

    review = models.Review(
        user_id=user.id,
        unit_id=req.unit_id,
        rating=req.rating,
        comment=req.comment,
        sentiment_score=sentiment.get("compound"),
        sentiment_label=sentiment.get("label"),
    )
    db.add(review)
    db.commit()
    db.refresh(review)
    return review


@router.get("/{unit_id}", response_model=List[schemas.ReviewOut])
def get_reviews(unit_id: str, db: Session = Depends(get_db)):
    return (
        db.query(models.Review)
        .filter(models.Review.unit_id == unit_id)
        .order_by(models.Review.created_at.desc())
        .limit(50)
        .all()
    )

