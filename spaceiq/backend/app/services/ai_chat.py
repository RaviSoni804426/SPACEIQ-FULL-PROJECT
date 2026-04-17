from __future__ import annotations

import json
import re
from typing import Any

from openai import AsyncOpenAI

from app.config import settings


SYSTEM_PROMPT = """
You are SpaceBot, an assistant for the SpaceIQ platform in Bangalore.
Help users find and book coworking spaces and sports venues.
Return valid JSON with:
- reply: string
- intent: find_space | book_space | price_inquiry | amenity_query | general
- params: object
Keep replies concise and friendly. Use Bangalore localities and rupees.
""".strip()


def _fallback_parse(message: str) -> dict[str, Any]:
    msg = message.lower()
    locality = None
    for candidate in ["hsr", "indiranagar", "koramangala", "whitefield", "jayanagar", "btm", "bellandur"]:
        if candidate in msg:
            locality = "HSR Layout" if candidate == "hsr" else candidate.title()
            break

    space_type = None
    if any(word in msg for word in ["cowork", "workspace", "desk", "office"]):
        space_type = "coworking"
    if any(word in msg for word in ["meeting room", "conference"]):
        space_type = "meeting_room"
    if any(word in msg for word in ["badminton", "football", "turf", "sports", "court"]):
        space_type = "sports"
    if "studio" in msg:
        space_type = "studio"

    intent = "general"
    if any(word in msg for word in ["find", "show", "near", "best", "cheap"]):
        intent = "find_space"
    if "book" in msg:
        intent = "book_space"
    if any(word in msg for word in ["price", "budget", "cost"]):
        intent = "price_inquiry"
    if any(word in msg for word in ["parking", "wifi", "projector", "cafeteria", "amenity"]):
        intent = "amenity_query"

    budget_match = re.search(r"(?:under|below|max|budget)\s*(?:rs|₹|inr)?\s*(\d+)", msg)
    params: dict[str, Any] = {}
    if locality:
        params["locality"] = [locality]
    if space_type:
        params["type"] = space_type
    if budget_match:
        params["price_max"] = float(budget_match.group(1))

    return {
        "reply": "I found a few Bangalore options that fit your request.",
        "intent": intent,
        "params": params,
    }


async def parse_chat(message: str, history: list[dict[str, str]]) -> dict[str, Any]:
    if not settings.openai_api_key:
        return _fallback_parse(message)

    client = AsyncOpenAI(api_key=settings.openai_api_key)
    messages: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]
    messages.extend(history[-10:])
    messages.append({"role": "user", "content": message})

    try:
        response = await client.chat.completions.create(
            model=settings.openai_model,
            temperature=0.2,
            response_format={"type": "json_object"},
            messages=messages,
        )
        content = response.choices[0].message.content or "{}"
        payload = json.loads(content)
        payload.setdefault("reply", "I found a few Bangalore spaces for you.")
        payload.setdefault("intent", "general")
        payload.setdefault("params", {})
        return payload
    except Exception:
        return _fallback_parse(message)
