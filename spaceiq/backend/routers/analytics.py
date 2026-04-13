from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db
from auth import require_admin
import models
from services.ml.forecasting import forecast_demand
from services.ml.recommender import recommend
from services.ml.anomaly import detect_anomalies

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/overview")
def overview(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    total_bookings = db.query(func.count(models.Booking.id)).scalar()
    total_revenue = db.query(func.sum(models.Booking.total_amount)).filter(
        models.Booking.status == "confirmed"
    ).scalar() or 0
    total_users = db.query(func.count(models.User.id)).scalar()
    avg_rating = db.query(func.avg(models.Review.rating)).scalar()

    return {
        "total_bookings": total_bookings,
        "total_revenue": round(total_revenue, 2),
        "total_users": total_users,
        "avg_rating": round(avg_rating or 0, 2),
    }


@router.get("/forecast/{unit_id}")
def get_forecast(unit_id: str, _admin=Depends(require_admin), db: Session = Depends(get_db)):
    return {"unit_id": unit_id, "forecast": forecast_demand(unit_id, db)}


@router.get("/recommend/{user_id}")
def get_recommendations(user_id: str, db: Session = Depends(get_db)):
    return {"recommendations": recommend(user_id, db)}


@router.get("/anomalies")
def get_anomalies(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    return {"anomalies": detect_anomalies(db)}


@router.get("/revenue-by-category")
def revenue_by_category(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    rows = (
        db.query(models.Unit.category, func.sum(models.Booking.total_amount).label("revenue"))
        .join(models.Booking, models.Booking.unit_id == models.Unit.id)
        .filter(models.Booking.status == "confirmed")
        .group_by(models.Unit.category)
        .all()
    )
    return [{"category": r[0], "revenue": round(r[1] or 0, 2)} for r in rows]


@router.get("/bookings-heatmap")
def bookings_heatmap(_admin=Depends(require_admin), db: Session = Depends(get_db)):
    """Returns booking counts by hour-of-day and day-of-week."""
    bookings = db.query(models.Booking).filter(models.Booking.status == "confirmed").all()
    heatmap = {}
    for b in bookings:
        key = f"{b.start_time.weekday()}-{b.start_time.hour}"
        heatmap[key] = heatmap.get(key, 0) + 1
    return heatmap
