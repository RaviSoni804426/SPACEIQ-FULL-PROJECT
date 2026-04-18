from __future__ import annotations

from datetime import date as date_type
import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy import Select, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import SlotStatus, Space, SpaceType
from app.schemas import SpaceDetail, SpaceSummary, TimeSlotOut
from app.services.slot_manager import ensure_slots_for_date, sweep_expired_holds
from app.utils.errors import api_error
from app.utils.serializers import serialize_space


router = APIRouter(prefix="/api/spaces", tags=["spaces"])


def _normalize_multi(values: list[str] | None) -> list[str]:
    if not values:
        return []
    normalized: list[str] = []
    for value in values:
        normalized.extend([item.strip() for item in value.split(",") if item.strip()])
    return normalized


async def _search_spaces(
    session: AsyncSession,
    *,
    search_query: str | None = None,
    space_type: SpaceType | None = None,
    locality: list[str] | None = None,
    price_min: float | None = None,
    price_max: float | None = None,
    rating: float | None = None,
    amenities: list[str] | None = None,
    sort: str = "relevance",
) -> list[Space]:
    query: Select[tuple[Space]] = select(Space).where(Space.is_active.is_(True))
    if space_type:
        query = query.where(Space.type == space_type)
    if locality:
        query = query.where(func.lower(Space.locality).in_([item.lower() for item in locality]))
    if price_min is not None:
        query = query.where(Space.price_per_hour >= price_min)
    if price_max is not None:
        query = query.where(Space.price_per_hour <= price_max)
    if rating is not None:
        query = query.where(Space.rating >= rating)
    if search_query:
        pattern = f"%{search_query.lower()}%"
        query = query.where(
            or_(
                func.lower(Space.name).like(pattern),
                func.lower(func.coalesce(Space.locality, "")).like(pattern),
                func.lower(func.coalesce(Space.address, "")).like(pattern),
            )
        )

    if sort == "price_asc":
        query = query.order_by(Space.price_per_hour.asc())
    elif sort == "rating":
        query = query.order_by(Space.rating.desc().nullslast())
    else:
        query = query.order_by(Space.rating.desc().nullslast(), Space.total_reviews.desc(), Space.created_at.desc())

    result = await session.execute(query.limit(24))
    spaces = list(result.scalars().all())

    amenity_filters = {value.lower() for value in amenities or []}
    if amenity_filters:
        spaces = [
            space
            for space in spaces
            if amenity_filters.issubset({amenity.lower() for amenity in (space.amenities or [])})
        ]
    return spaces


@router.get("", response_model=list[SpaceSummary])
async def list_spaces(
    q: str | None = Query(default=None, alias="search_query"),
    type: SpaceType | None = None,
    locality: list[str] = Query(default=[]),
    price_min: float | None = None,
    price_max: float | None = None,
    rating: float | None = None,
    amenities: list[str] = Query(default=[]),
    available_on: date_type | None = Query(default=None, alias="date"),
    sort: str = "relevance",
    session: AsyncSession = Depends(get_db),
) -> list[SpaceSummary]:
    normalized_locality = _normalize_multi(locality)
    normalized_amenities = _normalize_multi(amenities)

    spaces = await _search_spaces(
        session,
        search_query=q,
        space_type=type,
        locality=normalized_locality,
        price_min=price_min,
        price_max=price_max,
        rating=rating,
        amenities=normalized_amenities,
        sort=sort,
    )
    await sweep_expired_holds(session)
    response: list[SpaceSummary] = []
    for space in spaces:
        availability_count = None
        if available_on:
            slots = await ensure_slots_for_date(session, space, available_on)
            availability_count = len([slot for slot in slots if slot.status == SlotStatus.available])
        response.append(SpaceSummary.model_validate(serialize_space(space, availability_count)))
    return response


@router.get("/{space_id}", response_model=SpaceDetail)
async def get_space(
    space_id: str,
    booking_date: date_type | None = Query(default=None, alias="date"),
    session: AsyncSession = Depends(get_db),
) -> SpaceDetail:
    result = await session.execute(select(Space).where(Space.id == uuid.UUID(space_id), Space.is_active.is_(True)))
    space = result.scalar_one_or_none()
    if not space:
        raise api_error(404, "Space not found", "space_not_found")

    target_date = booking_date or date_type.today()
    await sweep_expired_holds(session)
    slots = await ensure_slots_for_date(session, space, target_date)
    payload = serialize_space(
        space,
        availability_count=len([slot for slot in slots if slot.status == SlotStatus.available]),
    )
    payload["available_slots"] = [TimeSlotOut.model_validate(slot) for slot in slots]
    return SpaceDetail.model_validate(payload)
