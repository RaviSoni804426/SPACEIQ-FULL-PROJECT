from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import Optional, List

from config import settings
from city_policy import BANGALORE_QUERY_VALUES, normalize_bangalore_city
from database import get_db
import models, schemas

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("/", response_model=List[schemas.LocationOut])
def list_locations(
    city: Optional[str] = None,
    area: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = db.query(models.Location).filter(models.Location.is_active == True)
    if city:
        try:
            normalize_bangalore_city(city)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
    q = q.filter(or_(*(models.Location.city.ilike(value) for value in BANGALORE_QUERY_VALUES)))
    if area:
        q = q.filter(models.Location.area.ilike(f"%{area}%"))
    return q.all()


@router.get("/launch-readiness")
def launch_readiness(db: Session = Depends(get_db)):
    locations = (
        db.query(models.Location)
        .filter(
            models.Location.is_active == True,
            or_(*(models.Location.city.ilike(value) for value in BANGALORE_QUERY_VALUES)),
        )
        .all()
    )
    location_ids = [row.id for row in locations]

    units = []
    if location_ids:
        units = (
            db.query(models.Unit)
            .filter(models.Unit.is_active == True, models.Unit.location_id.in_(location_ids))
            .all()
        )

    count_by_category: dict[str, int] = {}
    for unit in units:
        key = (unit.category or "other").lower()
        count_by_category[key] = count_by_category.get(key, 0) + 1

    venue_count = len(locations)
    in_target_range = settings.launch_min_verified_venues <= venue_count <= settings.launch_max_verified_venues
    priority_ready = count_by_category.get("coworking", 0) > 0 and count_by_category.get("sports", 0) > 0

    return {
        "city_scope": "Bengaluru",
        "venue_count": venue_count,
        "unit_count": len(units),
        "category_unit_counts": count_by_category,
        "target_range": {
            "min_verified_venues": settings.launch_min_verified_venues,
            "max_verified_venues": settings.launch_max_verified_venues,
            "in_range": in_target_range,
        },
        "priority_categories_ready": priority_ready,
        "booking_mode": settings.booking_mode,
        "real_payments_enabled": settings.real_payments_enabled,
    }


@router.get("/{location_id}", response_model=schemas.LocationOut)
def get_location(location_id: str, db: Session = Depends(get_db)):
    loc = (
        db.query(models.Location)
        .filter(
            models.Location.id == location_id,
            models.Location.is_active == True,
            or_(*(models.Location.city.ilike(value) for value in BANGALORE_QUERY_VALUES)),
        )
        .first()
    )
    if not loc:
        raise HTTPException(404, "Location not found")
    return loc


@router.get("/{location_id}/units", response_model=List[schemas.UnitOut])
def get_units(
    location_id: str,
    category: Optional[str] = None,
    db: Session = Depends(get_db),
):
    q = (
        db.query(models.Unit)
        .join(models.Location, models.Unit.location_id == models.Location.id)
        .filter(
            models.Unit.location_id == location_id,
            models.Unit.is_active == True,
            models.Location.is_active == True,
            or_(*(models.Location.city.ilike(value) for value in BANGALORE_QUERY_VALUES)),
        )
    )
    if category:
        q = q.filter(models.Unit.category == category)
    units = q.all()

    category_priority = {"coworking": 0, "sports": 1}
    units.sort(
        key=lambda unit: (
            category_priority.get((unit.category or "").lower(), 99),
            float(unit.base_price or 0),
            -(int(unit.capacity or 0)),
        )
    )
    return units


