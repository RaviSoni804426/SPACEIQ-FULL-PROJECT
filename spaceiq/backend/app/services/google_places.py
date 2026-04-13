from __future__ import annotations

import logging
import re
from decimal import Decimal

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models import Space, SpaceType
from app.services.demo_inventory import upsert_demo_inventory
from app.utils.errors import api_error


logger = logging.getLogger(__name__)

BANGALORE_CENTER = {"latitude": 12.9716, "longitude": 77.5946}
LOCALITY_MULTIPLIERS = {
    "indiranagar": 1.35,
    "koramangala": 1.25,
    "hsr layout": 1.15,
    "whitefield": 1.2,
    "jayanagar": 1.1,
    "btm": 1.0,
    "bellandur": 1.1,
}
KNOWN_LOCALITIES = tuple(LOCALITY_MULTIPLIERS.keys())


def _space_type_from_google(types: list[str]) -> SpaceType:
    haystack = " ".join(types).lower()
    if any(word in haystack for word in ("stadium", "arena", "sports", "court", "field", "gym")):
        return SpaceType.sports
    if "studio" in haystack:
        return SpaceType.studio
    if any(word in haystack for word in ("meeting_room", "conference_center")):
        return SpaceType.meeting_room
    return SpaceType.coworking


def _detect_locality(address: str) -> str:
    address_lower = address.lower()
    for locality in KNOWN_LOCALITIES:
        if locality in address_lower:
            return locality.title()
    parts = [part.strip() for part in address.split(",") if part.strip()]
    return parts[-3] if len(parts) >= 3 else "Bangalore"


def _estimate_price(space_type: SpaceType, locality: str) -> Decimal:
    base_price = {
        SpaceType.coworking: 550,
        SpaceType.sports: 900,
        SpaceType.meeting_room: 1200,
        SpaceType.studio: 1400,
    }[space_type]
    multiplier = LOCALITY_MULTIPLIERS.get(locality.lower(), 1.0)
    return Decimal(str(round(base_price * multiplier, 2)))


def _default_hours(space_type: SpaceType) -> dict[str, list[str]]:
    if space_type == SpaceType.sports:
        window = ["06:00", "22:00"]
    elif space_type == SpaceType.meeting_room:
        window = ["08:00", "21:00"]
    elif space_type == SpaceType.studio:
        window = ["09:00", "21:00"]
    else:
        window = ["08:00", "20:00"]
    return {day: window for day in ("mon", "tue", "wed", "thu", "fri", "sat", "sun")}


def _amenities_from_types(types: list[str], space_type: SpaceType) -> list[str]:
    amenities = {"Parking", "AC"}
    haystack = " ".join(types).lower()
    if space_type in {SpaceType.coworking, SpaceType.meeting_room}:
        amenities.update({"WiFi", "Projector", "Cafeteria"})
    if "sports" in haystack or space_type == SpaceType.sports:
        amenities.update({"Floodlights", "Washroom"})
    if space_type == SpaceType.studio:
        amenities.update({"Power Backup", "Soundproofing"})
    return sorted(amenities)


def _photo_urls(photos: list[dict]) -> list[str]:
    if not settings.google_places_api_key:
        return []
    urls: list[str] = []
    for photo in photos[:5]:
        name = photo.get("name")
        if name:
            urls.append(
                f"https://places.googleapis.com/v1/{name}/media?maxHeightPx=900&key={settings.google_places_api_key}"
            )
    return urls


def _clean_phone(value: str | None) -> str | None:
    if not value:
        return None
    return re.sub(r"\s+", " ", value).strip()


async def _fetch_place_details(client: httpx.AsyncClient, place_id: str) -> dict:
    response = await client.get(
        f"https://places.googleapis.com/v1/places/{place_id}",
        headers={
            "X-Goog-Api-Key": settings.google_places_api_key,
            "X-Goog-FieldMask": ",".join(
                [
                    "id",
                    "displayName",
                    "formattedAddress",
                    "location",
                    "rating",
                    "userRatingCount",
                    "websiteUri",
                    "nationalPhoneNumber",
                    "photos",
                    "types",
                ]
            ),
        },
        timeout=30.0,
    )
    response.raise_for_status()
    return response.json()


async def sync_google_places(session: AsyncSession, queries: list[str]) -> dict:
    if not settings.google_places_enabled:
        if not settings.is_production:
            logger.info("google_places_not_configured_seed_demo_inventory")
            return await upsert_demo_inventory(session)
        raise api_error(503, "Google Places API key is not configured", "google_places_not_configured")

    synced = 0
    synced_ids: list[str] = []

    async with httpx.AsyncClient() as client:
        for query in queries:
            response = await client.post(
                "https://places.googleapis.com/v1/places:searchText",
                headers={
                    "X-Goog-Api-Key": settings.google_places_api_key,
                    "X-Goog-FieldMask": ",".join(
                        [
                            "places.id",
                            "places.displayName",
                            "places.formattedAddress",
                            "places.location",
                            "places.types",
                        ]
                    ),
                },
                json={
                    "textQuery": query,
                    "languageCode": "en",
                    "pageSize": 12,
                    "locationBias": {"circle": {"center": BANGALORE_CENTER, "radius": 25000.0}},
                },
                timeout=30.0,
            )
            response.raise_for_status()

            for item in response.json().get("places", []):
                place_id = item.get("id")
                if not place_id or place_id in synced_ids:
                    continue

                details = await _fetch_place_details(client, place_id)
                name = (details.get("displayName") or {}).get("text") or "Unnamed Space"
                address = details.get("formattedAddress") or "Bangalore"
                types = details.get("types") or []
                space_type = _space_type_from_google(types)
                locality = _detect_locality(address)
                location = details.get("location") or {}

                result = await session.execute(select(Space).where(Space.google_place_id == place_id))
                space = result.scalar_one_or_none()
                if space is None:
                    space = Space(google_place_id=place_id, name=name, type=space_type)
                    session.add(space)

                space.name = name
                space.type = space_type
                space.description = f"{name} in {locality}, Bangalore, sourced from Google Places."
                space.address = address
                space.city = "Bangalore"
                space.locality = locality
                space.latitude = location.get("latitude")
                space.longitude = location.get("longitude")
                space.price_per_hour = _estimate_price(space_type, locality)
                space.rating = details.get("rating")
                space.total_reviews = int(details.get("userRatingCount") or 0)
                space.amenities = _amenities_from_types(types, space_type)
                space.images = _photo_urls(details.get("photos") or [])
                space.operating_hours = _default_hours(space_type)
                space.website_url = details.get("websiteUri")
                space.phone_number = _clean_phone(details.get("nationalPhoneNumber"))
                space.source = "google_places"
                space.is_active = True
                synced += 1
                synced_ids.append(place_id)

    await session.commit()
    logger.info("google_places_sync_completed", extra={"synced": synced})
    return {"synced": synced}
