from __future__ import annotations

import json
import re
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


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class SpaceCard(BaseModel):
    id: str
    name: str
    type: str
    locality: str | None
    price_per_hour: float
    rating: float | None
    amenities: list[str]
    image_url: str | None


class ChatResponse(BaseModel):
    reply: str
    action: str = "chat"          # "chat" | "show_spaces" | "book_space"
    spaces: list[SpaceCard] = []  # populated when action == "show_spaces"
    book_space_id: str | None = None  # populated when action == "book_space"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_space(query: str, space: Space) -> float:
    value = 0.0
    haystack = " ".join([
        space.name.lower(),
        (space.locality or "").lower(),
        (space.description or "").lower(),
        space.type.value.lower(),
        " ".join((space.amenities or [])).lower(),
    ])
    for token in query.split():
        if len(token) > 2 and token in haystack:
            value += 1.0
    if any(k in query for k in ("cheap", "budget", "affordable")):
        value += max(0.0, 2000.0 - float(space.price_per_hour)) / 500.0
    if any(k in query for k in ("premium", "best", "top")):
        value += float(space.rating or 0) * 0.8
    value += float(space.rating or 0) * 0.4
    return value


def _recommend_spaces(message: str, spaces: list[Space], top_n: int = 4) -> list[Space]:
    if not spaces:
        return []
    query = message.lower()
    return sorted(spaces, key=lambda s: _score_space(query, s), reverse=True)[:top_n]


def _space_to_card(space: Space) -> SpaceCard:
    image_url = space.images[0] if space.images else None
    return SpaceCard(
        id=str(space.id),
        name=space.name,
        type=space.type.value,
        locality=space.locality,
        price_per_hour=float(space.price_per_hour),
        rating=space.rating,
        amenities=list(space.amenities or [])[:5],
        image_url=image_url,
    )


_BOOKING_KEYWORDS = {"book", "reserve", "schedule", "want to book", "i want", "book this", "book now"}
_RECOMMEND_KEYWORDS = {"recommend", "suggest", "find", "show", "list", "looking for", "need a", "any space", "coworking", "studio", "meeting room", "sports"}
_ANALYTICS_KEYWORDS = {"revenue", "kpi", "forecast", "growth", "analysis", "analytics", "customer", "segment", "churn", "retention"}


def _detect_intent(message: str) -> str:
    lower = message.lower()
    if any(k in lower for k in _BOOKING_KEYWORDS):
        return "book"
    if any(k in lower for k in _RECOMMEND_KEYWORDS):
        return "recommend"
    if any(k in lower for k in _ANALYTICS_KEYWORDS):
        return "analytics"
    return "general"


def _fallback_response(message: str, spaces: list[Space], analytics: dict[str, Any]) -> ChatResponse:
    intent = _detect_intent(message)
    overview = analytics.get("overview", {})

    if intent == "analytics":
        total_revenue = overview.get("total_revenue", 0)
        growth = overview.get("month_over_month_growth_pct")
        projected = overview.get("projected_next_30d_revenue", 0)
        growth_text = f"{growth:+.2f}%" if growth is not None else "insufficient data"
        reply = (
            f"Here is the latest revenue snapshot:\n"
            f"• Total revenue: ₹{total_revenue:,.0f}\n"
            f"• Month-over-month growth: {growth_text}\n"
            f"• Projected 30-day revenue: ₹{projected:,.0f}\n\n"
            "Ask me about customer segments or locality performance for deeper insights."
        )
        return ChatResponse(reply=reply, action="chat")

    if intent in ("recommend", "book"):
        picks = _recommend_spaces(message, spaces)
        if not picks:
            return ChatResponse(
                reply="I couldn't find matching spaces. Try asking for coworking, studio, meeting room, or sports spaces.",
                action="chat",
            )
        reply = "Here are the best spaces matching your request. Click **Book Now** on any to start the booking flow."
        return ChatResponse(
            reply=reply,
            action="show_spaces",
            spaces=[_space_to_card(s) for s in picks],
        )

    return ChatResponse(
        reply=(
            "I can help you:\n"
            "• **Find & book spaces** — try 'Show me coworking spaces in Indiranagar'\n"
            "• **Interpret analytics** — try 'What is the revenue forecast?'\n"
            "• **Get recommendations** — try 'Best budget meeting room under ₹500/hr'"
        ),
        action="chat",
    )


_GROQ_SYSTEM_PROMPT = """\
You are SpaceIQ AI — a smart booking and analytics assistant for a workspace marketplace in Bangalore.

Your capabilities:
1. Recommend spaces and help users book them.
2. Answer analytics questions using the KPI data provided.
3. Guide users through the booking process conversationally.

Rules:
- Always respond with valid JSON matching this schema:
  {
    "reply": "<friendly markdown-formatted message to the user>",
    "action": "<one of: chat | show_spaces | book_space>",
    "space_ids": ["<uuid>", ...]   // only when action=show_spaces, list the IDs of spaces to show
  }
- Use action="show_spaces" when the user wants to find or browse spaces. Include the IDs of the best matching spaces from the inventory.
- Use action="book_space" when the user explicitly says they want to book a specific space (e.g. "book this", "I want to book [name]"). Include a single space_id.
- Use action="chat" for analytics questions, greetings, and general conversation.
- Use INR (₹) currency. Be concise. Use bullet points for lists.
- Do NOT invent space names or IDs — only use IDs from the inventory snapshot below.
- If the user asks for a space type not in inventory, say so honestly.

Analytics KPIs:
{analytics_overview}

Inventory (id | name | type | locality | price/hr | rating):
{inventory}
"""


def _build_groq_system(spaces: list[Space], analytics: dict[str, Any]) -> str:
    inventory_lines = [
        f"{space.id} | {space.name} | {space.type.value} | {space.locality or 'Bangalore'} | ₹{float(space.price_per_hour):,.0f} | {space.rating or 'N/A'}"
        for space in spaces[:20]
    ]
    return _GROQ_SYSTEM_PROMPT.format(
        analytics_overview=json.dumps(analytics.get("overview", {}), default=str),
        inventory="\n".join(inventory_lines),
    )


def _parse_groq_response(raw: str, spaces: list[Space]) -> ChatResponse:
    """Parse the JSON response from Groq and build a ChatResponse."""
    # Strip markdown code fences if present
    cleaned = re.sub(r"```(?:json)?", "", raw).strip().rstrip("`").strip()
    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError:
        # Groq didn't return valid JSON — treat as plain chat reply
        return ChatResponse(reply=raw, action="chat")

    reply = data.get("reply", raw)
    action = data.get("action", "chat")
    space_ids: list[str] = data.get("space_ids", [])

    space_map = {str(s.id): s for s in spaces}

    if action == "show_spaces" and space_ids:
        matched = [space_map[sid] for sid in space_ids if sid in space_map]
        if not matched:
            # IDs hallucinated — fall back to keyword scoring
            matched = _recommend_spaces(reply, spaces)
        return ChatResponse(
            reply=reply,
            action="show_spaces",
            spaces=[_space_to_card(s) for s in matched[:4]],
        )

    if action == "book_space" and space_ids:
        sid = space_ids[0]
        if sid in space_map:
            return ChatResponse(reply=reply, action="book_space", book_space_id=sid)

    return ChatResponse(reply=reply, action="chat")


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.post("/chat", response_model=ChatResponse)
async def ai_chatbot(request: ChatRequest, db: AsyncSession = Depends(get_db)) -> ChatResponse:
    spaces_result = await db.execute(select(Space).where(Space.is_active.is_(True)).limit(30))
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
        return _fallback_response(request.message, spaces, analytics)

    system_prompt = _build_groq_system(spaces, analytics)

    # Build conversation history for multi-turn context
    messages: list[dict[str, str]] = [{"role": "system", "content": system_prompt}]
    for msg in request.history[-6:]:  # keep last 6 turns for context
        messages.append({"role": msg.role, "content": msg.content})
    messages.append({"role": "user", "content": request.message})

    try:
        chat_completion = client.chat.completions.create(
            messages=messages,  # type: ignore[arg-type]
            model="llama3-8b-8192",
            temperature=0.4,
            max_tokens=500,
        )
        raw = chat_completion.choices[0].message.content or ""
        return _parse_groq_response(raw, spaces)
    except Exception:
        # Groq unavailable — use rule-based fallback
        return _fallback_response(request.message, spaces, analytics)


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