"""
Lightweight dynamic pricing.

This keeps the "smart pricing" idea without depending on scikit-learn models.
"""
from datetime import datetime



def get_dynamic_price(base_price: float, start_time: datetime, occupancy_rate: float = 0.5) -> float:
    occupancy_rate = max(0.0, min(1.0, occupancy_rate))
    days_ahead = max(0, (start_time.date() - datetime.utcnow().date()).days)

    multiplier = 1.0
    if start_time.hour in {8, 9, 18, 19, 20}:
        multiplier += 0.15
    if start_time.weekday() >= 5:
        multiplier += 0.1

    multiplier += occupancy_rate * 0.35
    multiplier -= min(days_ahead, 21) * 0.01
    multiplier = max(0.8, min(1.8, multiplier))
    return round(base_price * multiplier, 2)
