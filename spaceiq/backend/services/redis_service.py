import json
import redis as redis_lib
from fastapi import HTTPException
from config import settings

# Gracefully handle missing Redis — pool is created lazily
_pool = None

def _get_pool():
    global _pool
    if _pool is None:
        try:
            _pool = redis_lib.ConnectionPool.from_url(settings.redis_url, decode_responses=True)
        except Exception:
            _pool = None
    return _pool


def get_redis() -> redis_lib.Redis:
    pool = _get_pool()
    if pool is None:
        raise HTTPException(503, "Redis is not available. Booking holds and chat sessions require Redis.")
    return redis_lib.Redis(connection_pool=pool)


# ── Unit Hold (atomic, prevents race conditions) ──────────────────────────────

def hold_unit(unit_id: str, slot_key: str, user_id: str) -> bool:
    """
    Atomically set a hold key with 5-minute TTL.
    Uses SET NX EX — single uninterruptible Redis command.
    Raises 409 if someone else already holds this slot.
    """
    r = get_redis()
    key = f"hold:{unit_id}:{slot_key}"
    acquired = r.set(key, str(user_id), nx=True, ex=300)
    if not acquired:
        raise HTTPException(409, "This slot was just taken! Try another time slot.")
    return True


def release_hold(unit_id: str, slot_key: str):
    r = get_redis()
    r.delete(f"hold:{unit_id}:{slot_key}")


def is_held(unit_id: str, slot_key: str) -> bool:
    r = get_redis()
    return r.exists(f"hold:{unit_id}:{slot_key}") > 0


# ── Chat Session State ────────────────────────────────────────────────────────

def get_session(user_id: str) -> dict:
    r = get_redis()
    raw = r.get(f"session:{user_id}")
    return json.loads(raw) if raw else {}


def save_session(user_id: str, session: dict, ttl: int = 1800):
    r = get_redis()
    r.set(f"session:{user_id}", json.dumps(session), ex=ttl)


def clear_session(user_id: str):
    r = get_redis()
    r.delete(f"session:{user_id}")
