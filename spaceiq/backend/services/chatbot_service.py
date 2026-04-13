"""
Lightweight chatbot helpers.

The original project depended on an external LLM for intent extraction and
response generation. For local development we keep the chat useful with a
deterministic rules-based layer that works without extra services.
"""
from __future__ import annotations

import re
from datetime import date, datetime, timedelta


AREA_KEYWORDS = ["koramangala", "indiranagar", "hsr", "whitefield", "bengaluru"]
CATEGORY_KEYWORDS = {
    "sports": ["sport", "court", "badminton", "football", "tennis", "squash"],
    "coworking": ["coworking", "desk", "office", "workspace", "meeting room"],
    "events": ["event", "hall", "conference", "party", "venue"],
    "studio": ["studio", "shoot", "recording"],
    "parking": ["parking", "car park"],
}


def _detect_intent(message: str) -> str:
    msg = message.lower()
    if any(
        phrase in msg
        for phrase in [
            "book for me",
            "book this for me",
            "book it for me",
            "go ahead and book",
            "confirm booking",
            "book this",
        ]
    ):
        return "book_for_me"
    if re.search(r"\bbook\s+(first|second|third|1|2|3)\b", msg) or re.search(r"\b(first|second|third)\s+option\b", msg):
        return "book_for_me"
    if any(word in msg for word in ["recommend", "suggest", "best"]):
        if _detect_category(message) or _detect_area(message):
            return "search"
        return "recommend"
    if any(word in msg for word in ["cancel", "refund"]):
        return "cancel"
    if any(word in msg for word in ["book", "reserve", "available", "find", "search", "show"]):
        return "search"
    return "chitchat"


def _detect_category(message: str) -> str | None:
    msg = message.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(keyword in msg for keyword in keywords):
            return category
    return None


def _detect_area(message: str) -> str | None:
    msg = message.lower()
    for area in AREA_KEYWORDS:
        if area in msg:
            return "HSR Layout" if area == "hsr" else area.title()
    return None


def _detect_budget(message: str) -> float | None:
    match = re.search(r"(?:under|below|max|budget)\s*(?:rs|inr)?\.?\s*(\d+)", message.lower())
    return float(match.group(1)) if match else None


def _detect_people(message: str) -> int | None:
    match = re.search(r"(\d+)\s*(?:people|persons|pax|seats?)", message.lower())
    return int(match.group(1)) if match else None


def _detect_date(message: str) -> str | None:
    msg = message.lower()
    today = date.today()
    if "today" in msg:
        return today.isoformat()
    if "tomorrow" in msg:
        return (today + timedelta(days=1)).isoformat()

    for offset in range(7):
        candidate = today + timedelta(days=offset)
        weekday = candidate.strftime("%A").lower()
        if weekday in msg:
            return candidate.isoformat()
    return None


def _detect_time_range(message: str) -> tuple[str | None, str | None, int | None]:
    msg = message.lower()
    time_match = re.search(r"(\d{1,2})(?::(\d{2}))?\s*(am|pm)?", msg)
    duration_match = re.search(r"(\d+)\s*hour", msg)
    duration_hours = int(duration_match.group(1)) if duration_match else None
    if not time_match:
        return None, None, duration_hours

    hour = int(time_match.group(1))
    minute = int(time_match.group(2) or 0)
    meridiem = time_match.group(3)
    if meridiem == "pm" and hour != 12:
        hour += 12
    if meridiem == "am" and hour == 12:
        hour = 0
    start = f"{hour:02d}:{minute:02d}"

    end = None
    if duration_hours is not None:
        start_dt = datetime.combine(date.today(), datetime.strptime(start, "%H:%M").time())
        end = (start_dt + timedelta(hours=duration_hours)).strftime("%H:%M")
    return start, end, duration_hours


async def extract_intent(message: str) -> dict:
    time_start, time_end, duration_hours = _detect_time_range(message)
    return {
        "intent": _detect_intent(message),
        "category": _detect_category(message),
        "location_area": _detect_area(message),
        "date": _detect_date(message),
        "time_start": time_start,
        "time_end": time_end,
        "duration_hours": duration_hours,
        "budget_max": _detect_budget(message),
        "people_count": _detect_people(message),
        "search_phrase": message.strip(),
        "amenities": [],
        "missing_required": [],
    }


def check_missing_slots(state: dict, intent: str) -> str | None:
    if intent not in {"book", "search", "book_for_me"}:
        return None
    if not any([state.get("category"), state.get("location_area"), state.get("search_phrase")]):
        return "Tell me an area or a type of space, like coworking in Indiranagar, sports in Koramangala, or event space in HSR Layout."
    return None


def merge_state(existing: dict, new_data: dict) -> dict:
    merged = dict(existing)
    for key, value in new_data.items():
        if value not in (None, [], "") and key != "missing_required":
            merged[key] = value
    return merged


async def generate_search_response(units: list, booking_state: dict) -> str:
    if not units:
        return "I could not find a matching space right now. Try another area, category, or budget."

    best = units[0]
    area = best.get("area") or best.get("location") or "Bengaluru"
    requested_people = booking_state.get("people_count")
    budget = booking_state.get("budget_max")
    context_bits = []
    if requested_people:
        context_bits.append(f"for around {requested_people} people")
    if budget:
        context_bits.append(f"within about Rs {float(budget):.0f}")
    context_text = f" {', '.join(context_bits)}" if context_bits else ""

    lines = []
    for option in units[:3]:
        price = option.get("price") or option.get("base_price") or 0
        option_area = option.get("area") or option.get("location") or "Bengaluru"
        lines.append(
            f"{option['name']} in {option_area} for Rs {price:.0f}/hr"
        )

    shortlist = "; ".join(lines)
    return (
        f"I found a shortlist{context_text}. My top suggestion is {best['name']} in {area} because it is the strongest balance of fit and price. "
        f"Here are the best options: {shortlist}. If you want me to continue, just say book for me, book first option, or book second option."
    )


async def general_reply(message: str, history: list) -> str:
    _ = history
    msg = message.lower()
    if "hello" in msg or "hi" in msg:
        return "Hi! Tell me the area, space type, team size, or budget, and I will suggest the best options."
    if "who are you" in msg or "what can you do" in msg:
        return "I am the SpaceIQ booking assistant. I can suggest spaces by area, type, group size, and budget, and I can also help book one."
    if "cheap" in msg or "budget" in msg:
        return "Tell me the area or type of space you want, and I will suggest the lowest-cost options first."
    if "best" in msg or "top" in msg:
        return "Tell me the area or category you want, and I will rank the strongest options based on fit and price."
    if "policy" in msg or "cancel" in msg:
        return "Bookings can be cancelled from the My Bookings page, and future slots are the safest ones to cancel early."
    return "I can help you search for a space by area, category, budget, or group size. For example, say coworking in Indiranagar for 4 people."
