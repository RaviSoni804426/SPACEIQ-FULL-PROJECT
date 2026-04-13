"""
Lightweight anomaly detection using mean and standard deviation.
"""
from collections import defaultdict
from datetime import datetime, timedelta
from statistics import mean, pstdev

from sqlalchemy.orm import Session

import models



def detect_anomalies(db: Session, lookback_days: int = 30) -> list:
    since = datetime.utcnow() - timedelta(days=lookback_days)
    bookings = db.query(models.Booking).filter(models.Booking.created_at >= since).all()
    if not bookings:
        return []

    daily = defaultdict(lambda: defaultdict(int))
    for booking in bookings:
        daily[booking.unit_id][booking.created_at.date().isoformat()] += 1

    anomalies = []
    for unit_id, day_counts in daily.items():
        counts = list(day_counts.values())
        if len(counts) < 5:
            continue

        avg = mean(counts)
        deviation = pstdev(counts) or 1.0
        unit = db.query(models.Unit).filter(models.Unit.id == unit_id).first()

        for day, count in day_counts.items():
            z_score = (count - avg) / deviation
            if abs(z_score) >= 1.75:
                anomalies.append(
                    {
                        "unit_id": unit_id,
                        "unit_name": unit.name if unit else "Unknown",
                        "date": day,
                        "booking_count": count,
                        "anomaly_score": round(abs(z_score), 4),
                        "type": "high_demand" if count > avg else "low_demand",
                    }
                )

    anomalies.sort(key=lambda item: item["anomaly_score"], reverse=True)
    return anomalies
