"""
Lightweight recommendations based on the user's confirmed booking history.
"""
from collections import Counter

from sqlalchemy.orm import Session

import models



def recommend(user_id: str, db: Session, top_k: int = 5) -> list:
    bookings = (
        db.query(models.Booking)
        .filter(models.Booking.user_id == user_id, models.Booking.status == "confirmed")
        .limit(25)
        .all()
    )
    units = db.query(models.Unit).filter(models.Unit.is_active == True).all()
    if not units:
        return []

    if not bookings:
        return [
            {
                "unit_id": unit.id,
                "name": unit.name,
                "category": unit.category,
                "location": unit.location.name if unit.location else "",
                "base_price": unit.base_price,
                "score": 0.5,
            }
            for unit in units[:top_k]
        ]

    category_counts = Counter(booking.unit.category for booking in bookings if booking.unit)
    average_price = sum(booking.unit.base_price for booking in bookings if booking.unit) / max(len(bookings), 1)

    scored = []
    for unit in units:
        category_score = category_counts.get(unit.category, 0) * 1.5
        price_score = max(0.0, 1.0 - abs(unit.base_price - average_price) / max(average_price, 1))
        score = round(category_score + price_score, 4)
        scored.append(
            {
                "unit_id": unit.id,
                "name": unit.name,
                "category": unit.category,
                "location": unit.location.name if unit.location else "",
                "base_price": unit.base_price,
                "score": score,
            }
        )

    scored.sort(key=lambda item: item["score"], reverse=True)
    return scored[:top_k]
