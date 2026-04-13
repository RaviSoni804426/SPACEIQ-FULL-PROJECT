from __future__ import annotations

from fastapi import APIRouter, Body, Depends, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.schemas import ChatRequest, ChatResponse, SpaceSummary
from app.services.ai_chat import parse_chat
from app.utils.rate_limit import limiter
from app.utils.serializers import serialize_space
from app.routers.spaces import _search_spaces


router = APIRouter(prefix="/api/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
@limiter.limit(settings.chat_rate_limit)
async def chat(
    request: Request,
    payload_data: dict = Body(...),
    session: AsyncSession = Depends(get_db),
) -> ChatResponse:
    payload = ChatRequest.model_validate(payload_data)
    parsed = await parse_chat(payload.message, [turn.model_dump() for turn in payload.history])
    params = parsed.get("params") or {}
    space_type = params.get("type")
    structured_filters_present = any(
        params.get(key)
        for key in ("type", "locality", "amenities", "price_min", "price_max", "rating")
    )
    search_query = None
    if parsed.get("intent") == "find_space":
        search_query = params.get("search_query")
        if not search_query and not structured_filters_present:
            search_query = payload.message

    suggested = await _search_spaces(
        session,
        search_query=search_query,
        space_type=space_type,
        locality=params.get("locality") or [],
        price_max=params.get("price_max"),
        amenities=params.get("amenities") or [],
        sort="rating",
    )
    suggested_spaces = [SpaceSummary.model_validate(serialize_space(space)) for space in suggested[:3]]
    return ChatResponse(reply=parsed.get("reply", "I found a few Bangalore options for you."), intent=parsed.get("intent", "general"), suggested_spaces=suggested_spaces)
