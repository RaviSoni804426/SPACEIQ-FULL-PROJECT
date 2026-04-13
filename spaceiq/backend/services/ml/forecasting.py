"""
Lightweight demand forecasting based on recent weekday averages.
"""
from collections import Counter
from datetime import datetime, timedelta
from statistics import mean

from sqlalchemy.orm import Session

import models



def _daily_counts(unit_id: str, db: Session) -> Counter:
    bookings = (
        db.query(models.Booking)
        .filter(
            models.Booking.unit_id == unit_id,
            models.Booking.status.in_(["confirmed", "completed"]),
        )
        .all()
    )
    counts: Counter = Counter()
    for booking in bookings:
        counts[booking.start_time.date()] += 1
    return counts



def forecast_demand(unit_id: str, db: Session, periods: int = 30) -> list:
    counts = _daily_counts(unit_id, db)
    if not counts:
        return _synthetic_forecast(periods)

    values = list(counts.values())
    overall_average = mean(values)
    weekday_map: dict[int, list[int]] = {}
    for day, count in counts.items():
        weekday_map.setdefault(day.weekday(), []).append(count)

    today = datetime.utcnow().date()
    forecast = []
    for offset in range(periods):
        current_day = today + timedelta(days=offset)
        weekday_average = mean(weekday_map.get(current_day.weekday(), values))
        projected = round((overall_average * 0.4) + (weekday_average * 0.6), 2)
        spread = max(1.0, round(projected * 0.25, 2))
        forecast.append(
            {
                "date": current_day.isoformat(),
                "demand": max(0.0, projected),
                "lower": max(0.0, round(projected - spread, 2)),
                "upper": round(projected + spread, 2),
            }
        )
    return forecast



def _synthetic_forecast(periods: int = 30) -> list:
    today = datetime.utcnow().date()
    forecast = []
    for offset in range(periods):
        current_day = today + timedelta(days=offset)
        base = 5 if current_day.weekday() >= 5 else 3
        forecast.append(
            {
                "date": current_day.isoformat(),
                "demand": float(base),
                "lower": float(max(base - 1, 0)),
                "upper": float(base + 1),
            }
        )
    return forecast
