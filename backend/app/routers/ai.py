from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends
from groq import Groq
from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.database import get_db
from app.models import Booking, SearchEvent, Space
from app.services.analytics import build_analytics_payload

router = APIRouter(prefix="/ai", tags=["AI & Data Science"])

client = Groq(api_key=settings.groq_api_key) if settings.groq_api_key else None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


def _recommend_spaces_from_query(message: str, spaces: list[Space]) -> list[Space]:
    if not spaces:
        return []

    query = message.lower()

    def score(space: Space) -> float:
        value = 0.0
        haystack = " ".join(
            [
                space.name.lower(),
                (space.locality or "").lower(),
                (space.description or "").lower(),
                space.type.value.lower(),
                " ".join((space.amenities or [])).lower(),
            ]
        )

        for token in query.split():
            if token in haystack:
                value += 1.0

        if "cheap" in query or "budget" in query or "affordable" in query:
            value += max(0.0, 2000.0 - float(space.price_per_hour)) / 500.0
        if "premium" in query or "best" in query:
            value += float(space.rating or 0) * 0.8

        value += float(space.rating or 0) * 0.4
        return value

    return sorted(spaces, key=score, reverse=True)[:3]


def _fallback_chat_response(message: str, spaces: list[Space], analytics: dict[str, Any]) -> str:
    normalized = message.lower()
    overview = analytics.get("overview", {})

    if any(keyword in normalized for keyword in ["revenue", "kpi", "forecast", "growth", "analysis"]):
        total_revenue = overview.get("total_revenue", 0)
        growth = overview.get("month_over_month_growth_pct")
        projected = overview.get("projected_next_30d_revenue", 0)
        growth_text = f"{growth:+.2f}%" if growth is not None else "insufficient data"
        return (
            "Here is the latest revenue snapshot: "
            f"Total revenue is INR {total_revenue:,.2f}, month-over-month growth is {growth_text}, "
            f"and projected 30-day revenue is INR {projected:,.2f}. "
            "Ask me for customer segments or locality-level performance for deeper insights."
        )

    if any(keyword in normalized for keyword in ["recommend", "suggest", "space", "book"]):
        picks = _recommend_spaces_from_query(message, spaces)
        if not picks:
            return "I could not find matching spaces yet. Try asking for coworking, studio, meeting room, or sports recommendations."

        lines = ["Top picks based on your request:"]
        for space in picks:
            lines.append(
                f"- {space.name} ({space.type.value}) in {space.locality or 'Bangalore'} at INR {float(space.price_per_hour):,.0f}/hour"
            )
        lines.append("Tell me your budget and locality, and I will narrow this to one best option.")
        return "\n".join(lines)

    if any(keyword in normalized for keyword in ["customer", "segment", "churn", "retention"]):
        tiers = analytics.get("segmentation", {}).get("customer_tiers", [])
        if not tiers:
            return "Customer segmentation needs booking history. Run demo data seeding to unlock churn and retention insights."
        top = tiers[0]
        return (
            f"Top customer segment is '{top['segment']}' with {top['users']} users contributing INR {top['revenue']:,.2f}. "
            "You can use this to design retention and upsell campaigns."
        )

    return (
        "I can help with three tasks: space recommendations, revenue analytics, and customer segmentation. "
        "Try asking: 'Show forecast for next 14 days' or 'Recommend a budget coworking in Indiranagar'."
    )


@router.post("/chat", response_model=ChatResponse)
async def ai_chatbot(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    spaces_result = await db.execute(select(Space).where(Space.is_active.is_(True)).limit(20))
    spaces = list(spaces_result.scalars().all())

    bookings_result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.space), selectinload(Booking.review))
        .order_by(Booking.booking_date.asc())
    )
    bookings = list(bookings_result.scalars().all())

    search_events_count = await db.scalar(select(func.count(SearchEvent.id)))
    analytics = build_analytics_payload(bookings, int(search_events_count or 0))

    if not client:
        return ChatResponse(reply=_fallback_chat_response(request.message, spaces, analytics))

    spaces_context_lines = [
        f"- {space.name} | type={space.type.value} | locality={space.locality} | price_per_hour={float(space.price_per_hour):.2f} | rating={space.rating}"
        for space in spaces[:10]
    ]

    system_prompt = (
        "You are SpaceIQ AI, an analytics and booking assistant for a workspace marketplace. "
        "Answer with concise, practical recommendations. Use INR currency. "
        "If a user asks for analytics, use the provided KPI context and do not invent values.\n\n"
        f"Analytics overview: {analytics.get('overview', {})}\n"
        "Top recommendations from analytics engine:\n"
        + "\n".join([f"- {item}" for item in analytics.get("recommendations", [])])
        + "\n\nInventory snapshot:\n"
        + "\n".join(spaces_context_lines)
    )

    chat_completion = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": request.message},
        ],
        model="llama3-8b-8192",
        temperature=0.5,
        max_tokens=350,
    )

    return ChatResponse(reply=chat_completion.choices[0].message.content)


@router.get("/analytics")
async def analytics_overview(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:
    bookings_result = await db.execute(
        select(Booking)
        .options(selectinload(Booking.space), selectinload(Booking.review))
        .order_by(Booking.booking_date.asc())
    )
    bookings = list(bookings_result.scalars().all())
    search_events_count = await db.scalar(select(func.count(SearchEvent.id)))

    return build_analytics_payload(bookings, int(search_events_count or 0))