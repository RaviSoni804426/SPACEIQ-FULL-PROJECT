from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
import re
from database import get_db
from auth import get_current_user
from city_policy import BANGALORE_QUERY_VALUES
from config import settings
import models, schemas
from services import chatbot_service
from services.booking_service import (
    booking_conflict_exists,
    calculate_booking_price,
    create_confirmed_booking,
    create_pending_booking,
    get_active_unit,
)
from services.ml.recommender import recommend

router = APIRouter(prefix="/chat", tags=["chat"])

# In-memory session store (fallback when Redis unavailable)
_memory_sessions: dict = {}


def _get_session(user_id: str) -> dict:
    try:
        from services.redis_service import get_session
        return get_session(user_id)
    except Exception:
        return _memory_sessions.get(user_id, {})


def _save_session(user_id: str, session: dict):
    try:
        from services.redis_service import save_session
        save_session(user_id, session, ttl=1800)
    except Exception:
        _memory_sessions[user_id] = session


def _clear_session(user_id: str):
    try:
        from services.redis_service import clear_session
        clear_session(user_id)
    except Exception:
        _memory_sessions.pop(user_id, None)


def _message_is_booking_confirmation(message: str) -> bool:
    msg = message.lower().strip()
    confirmations = {
        "yes",
        "book it",
        "confirm",
        "haan",
        "ha",
        "sure",
        "ok",
        "okay",
        "book for me",
        "book this",
        "book this for me",
        "go ahead and book",
        "confirm booking",
    }
    if msg in confirmations:
        return True
    patterns = [
        r"\bbook\s+for\s+me\b",
        r"\bbook\s+this\b",
        r"\bbook\s+(first|second|third|1|2|3)\b",
        r"\bconfirm\b",
        r"\bgo\s+ahead\s+and\s+book\b",
        r"\b(first|second|third)\s+option\b",
    ]
    return any(re.search(pattern, msg) for pattern in patterns)


def _extract_option_index(message: str) -> int | None:
    msg = message.lower()
    ordinal_map = {
        "first": 0,
        "1st": 0,
        "one": 0,
        "top": 0,
        "best": 0,
        "second": 1,
        "2nd": 1,
        "two": 1,
        "third": 2,
        "3rd": 2,
        "three": 2,
    }
    for token, idx in ordinal_map.items():
        if re.search(rf"\b{re.escape(token)}\b", msg):
            return idx
    numeric_match = re.search(r"\boption\s*(\d+)\b|\bbook\s*(\d+)\b", msg)
    if numeric_match:
        raw = numeric_match.group(1) or numeric_match.group(2)
        idx = int(raw) - 1
        if idx >= 0:
            return idx
    return None


def _tokenize_search_terms(message: str) -> list[str]:
    stop_words = {
        "find",
        "show",
        "suggest",
        "book",
        "for",
        "me",
        "please",
        "need",
        "want",
        "space",
        "spaces",
        "area",
        "wise",
        "in",
        "the",
        "a",
        "an",
    }
    words = [
        word
        for word in "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in message.lower()).split()
        if len(word) > 2 and word not in stop_words
    ]
    return words[:5]


def _normalize_option(option: dict) -> dict:
    option_id = option.get("id") or option.get("unit_id")
    return {
        "id": option_id,
        "name": option.get("name", "Suggested space"),
        "category": option.get("category", "space"),
        "location": option.get("location", ""),
        "area": option.get("area", ""),
        "price": option.get("price", option.get("base_price", 0)),
        "capacity": option.get("capacity", 1),
        "score": option.get("score"),
    }


def _query_units(state: dict, original_message: str, db: Session) -> list[dict]:
    category = state.get("category")
    area = state.get("location_area")
    budget = state.get("budget_max")
    search_terms = _tokenize_search_terms(original_message)

    q = (
        db.query(models.Unit)
        .join(models.Location)
        .filter(
            models.Unit.is_active == True,
            models.Location.is_active == True,
            or_(*(models.Location.city.ilike(value) for value in BANGALORE_QUERY_VALUES)),
        )
    )
    if category:
        q = q.filter(models.Unit.category.ilike(f"%{category}%"))
    if area:
        q = q.filter(models.Location.area.ilike(f"%{area}%"))
    if budget:
        q = q.filter(models.Unit.base_price <= float(budget))

    units = q.limit(20).all()
    results = []
    for unit in units:
        haystack = " ".join(
            [
                unit.name.lower(),
                unit.category.lower(),
                (unit.location.name if unit.location else "").lower(),
                (unit.location.area if unit.location else "").lower(),
            ]
        )
        if search_terms and not all(term in haystack for term in search_terms if term not in {"tomorrow", "today"}):
            if not any(term in haystack for term in search_terms):
                continue
        results.append(
            {
                "id": unit.id,
                "name": unit.name,
                "category": unit.category,
                "location": unit.location.name if unit.location else "",
                "area": unit.location.area if unit.location else "",
                "price": unit.base_price,
                "capacity": unit.capacity,
            }
        )

    category_priority = {"coworking": 0, "sports": 1}
    results.sort(
        key=lambda unit: (
            category_priority.get((unit.get("category") or "").lower(), 99),
            unit["price"],
            -unit["capacity"],
        )
    )
    return results[:5]


def _resolve_booking_window(state: dict) -> tuple[datetime, datetime]:
    booking_date = state.get("date")
    start_text = state.get("time_start")
    duration_hours = int(state.get("duration_hours") or 1)

    if booking_date:
        base_date = datetime.strptime(booking_date, "%Y-%m-%d").date()
    else:
        base_date = (datetime.utcnow() + timedelta(days=1)).date()

    if start_text:
        start_time = datetime.strptime(start_text, "%H:%M").time()
    else:
        start_time = datetime.strptime("10:00", "%H:%M").time()

    start_dt = datetime.combine(base_date, start_time)
    end_dt = start_dt + timedelta(hours=max(duration_hours, 1))
    return start_dt, end_dt


def _slot_conflicts(unit_id: str, start_dt: datetime, end_dt: datetime, db: Session) -> bool:
    return booking_conflict_exists(unit_id, start_dt, end_dt, db)


def _book_selected_option(user: models.User, state: dict, db: Session) -> dict:
    options = [_normalize_option(option) for option in (state.get("options") or [])]
    if not options:
        raise HTTPException(400, "There is no suggestion ready to book yet.")

    selected = _normalize_option(state.get("selected_unit") or options[0])
    unit = get_active_unit(selected["id"], db)

    start_dt, end_dt = _resolve_booking_window(state)
    attempts = 0
    while _slot_conflicts(unit.id, start_dt, end_dt, db) and attempts < 12:
        start_dt += timedelta(hours=1)
        end_dt += timedelta(hours=1)
        attempts += 1

    if _slot_conflicts(unit.id, start_dt, end_dt, db):
        raise HTTPException(409, "I could not find an open slot for that suggestion right now.")

    price = calculate_booking_price(unit, start_dt, db)
    booking_status = "confirmed"
    token = None
    qr_image = None
    if settings.booking_mode.strip().lower() == "request":
        booking = create_pending_booking(
            user=user,
            unit=unit,
            start_time=start_dt,
            end_time=end_dt,
            amount=price,
            source="chat",
            order_id=f"order_req_{user.id[:8]}_{int(start_dt.timestamp())}",
            payment_id=None,
            db=db,
        )
        booking_status = "pending"
    else:
        booking, token, qr_image = create_confirmed_booking(
            user=user,
            unit=unit,
            start_time=start_dt,
            end_time=end_dt,
            amount=price,
            source="chat",
            order_id=f"order_chat_{user.id[:8]}_{int(start_dt.timestamp())}",
            payment_id=f"pay_chat_{unit.id[:8]}_{int(end_dt.timestamp())}",
            db=db,
        )

    state["selected_unit"] = _normalize_option(
        {
            "id": unit.id,
            "name": unit.name,
            "category": unit.category,
            "location": unit.location.name if unit.location else "",
            "area": unit.location.area if unit.location else "",
            "price": price,
            "capacity": unit.capacity,
        }
    )
    state["stage"] = "booked"
    state["last_booking"] = {
        "booking_id": booking.id,
        "unit_name": unit.name,
        "location_name": unit.location.name if unit.location else "",
        "area": unit.location.area if unit.location else "",
        "price": price,
        "start_time": booking.start_time.isoformat(),
        "end_time": booking.end_time.isoformat(),
        "status": booking_status,
        "qr_token": token,
        "qr_image_b64": qr_image,
    }
    return state["last_booking"]


@router.post("/", response_model=schemas.ChatResponse)
async def chat(
    req: schemas.ChatRequest,
    user: models.User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    session = _get_session(user.id)

    # Extract intent from message
    try:
        intent_data = await chatbot_service.extract_intent(req.message)
    except Exception as e:
        # If Groq API fails, do a basic keyword-based intent extraction
        intent_data = _fallback_intent(req.message)

    intent = intent_data.get("intent", "chitchat")

    # Merge with existing booking state
    existing_state = session.get("booking_state", {})
    new_state = chatbot_service.merge_state(existing_state, intent_data)
    session["booking_state"] = new_state

    history = session.get("history", [])
    history.append({"role": "user", "content": req.message})

    reply = ""
    action = None
    options = None
    booking = None

    if intent == "chitchat":
        try:
            reply = await chatbot_service.general_reply(req.message, history)
        except Exception:
            reply = _fallback_chitchat(req.message)

    elif intent == "recommend":
        recs = recommend(user.id, db)
        if recs:
            names = ", ".join(r["name"] for r in recs[:3])
            reply = f"Based on your history, I suggest {names}. If one of them looks good, just say book for me."
            options = [_normalize_option(rec) for rec in recs]
            session["booking_state"]["stage"] = "awaiting_confirmation"
            session["booking_state"]["options"] = options
            session["booking_state"]["selected_unit"] = options[0]
        else:
            reply = "I don't have enough booking history to make personalized recommendations yet. Try browsing our spaces!"

    elif intent in ("book", "search", "book_for_me"):
        option_index = _extract_option_index(req.message)
        if option_index is not None:
            available_options = session["booking_state"].get("options") or []
            if 0 <= option_index < len(available_options):
                session["booking_state"]["selected_unit"] = _normalize_option(available_options[option_index])
        missing = chatbot_service.check_missing_slots(new_state, intent)
        if missing and not _message_is_booking_confirmation(req.message):
            reply = missing
            action = "slot_filling"
        elif intent == "book_for_me" or _message_is_booking_confirmation(req.message):
            try:
                booking = _book_selected_option(user, session["booking_state"], db)
                if booking.get("status") == "pending":
                    reply = (
                        f"Request submitted for {booking['unit_name']} in {booking['area']} on "
                        f"{datetime.fromisoformat(booking['start_time']).strftime('%d %b %Y %I:%M %p')}. "
                        "The venue team will confirm availability before payment capture."
                    )
                else:
                    reply = (
                        f"Booked {booking['unit_name']} in {booking['area']} for "
                        f"{datetime.fromisoformat(booking['start_time']).strftime('%d %b %Y %I:%M %p')}. "
                        f"Your booking is confirmed."
                    )
                action = "booked"
            except HTTPException as exc:
                reply = exc.detail
                action = "booking_failed"
        else:
            units_dicts = [_normalize_option(option) for option in _query_units(new_state, req.message, db)]

            try:
                reply = await chatbot_service.generate_search_response(units_dicts, new_state)
            except Exception:
                if units_dicts:
                    reply = (
                        f"I found {len(units_dicts)} spaces matching your criteria. "
                        f"The best option is {units_dicts[0]['name']} at {units_dicts[0].get('area', 'Bengaluru')} "
                        f"for Rs {units_dicts[0]['price']}/hr. You can say book for me or book second option."
                    )
                else:
                    reply = "I couldn't find spaces matching your criteria. Try different filters?"

            session["booking_state"]["stage"] = "awaiting_confirmation" if units_dicts else "search_empty"
            session["booking_state"]["options"] = units_dicts
            if units_dicts:
                session["booking_state"]["selected_unit"] = units_dicts[0]
            options = units_dicts

    history.append({"role": "assistant", "content": reply})
    session["history"] = history[-20:]  # keep last 20 turns
    _save_session(user.id, session)

    return {"reply": reply, "action": action, "options": options, "booking": booking}


@router.delete("/session")
def clear_chat_session(user: models.User = Depends(get_current_user)):
    _clear_session(user.id)
    return {"cleared": True}


def _fallback_intent(message: str) -> dict:
    """Basic keyword-based intent extraction when AI is unavailable."""
    msg = message.lower()
    if (
        "book for me" in msg
        or "book this" in msg
        or re.search(r"\bbook\s+(first|second|third|1|2|3)\b", msg)
        or re.search(r"\b(first|second|third)\s+option\b", msg)
    ):
        return {"intent": "book_for_me", "missing_required": []}
    if any(w in msg for w in ["book", "reserve", "slot", "available"]):
        return {"intent": "search", "missing_required": []}
    if any(w in msg for w in ["recommend", "suggest", "best"]):
        return {"intent": "recommend", "missing_required": []}
    if any(w in msg for w in ["cancel", "void"]):
        return {"intent": "cancel", "missing_required": []}
    return {"intent": "chitchat", "missing_required": []}


def _fallback_chitchat(message: str) -> str:
    """Basic response when AI is unavailable."""
    return (
        "Hey! I'm IQ, your SpaceIQ assistant. I can help you find and book "
        "sports courts, coworking spaces, event halls, and more in Bengaluru. "
        "Try asking me something like 'find a coworking space in Koramangala' "
        "or 'book a badminton court for tomorrow'!"
    )

