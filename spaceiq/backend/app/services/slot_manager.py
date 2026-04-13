from __future__ import annotations

import json
import logging
import uuid
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal
from typing import Awaitable, Callable

from redis.asyncio import Redis
from redis.exceptions import RedisError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.config import settings
from app.models import Booking, BookingStatus, SlotStatus, Space, SpaceType, TimeSlot, User
from app.utils.errors import api_error


logger = logging.getLogger(__name__)
_redis_client: Redis | None = None
_redis_disabled = False


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def normalize_utc(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def _fallback_window(space_type: SpaceType) -> tuple[str, str]:
    if space_type == SpaceType.sports:
        return "06:00", "22:00"
    if space_type == SpaceType.meeting_room:
        return "08:00", "21:00"
    if space_type == SpaceType.studio:
        return "09:00", "21:00"
    return "08:00", "20:00"


async def get_redis() -> Redis | None:
    global _redis_client, _redis_disabled
    if _redis_disabled or not settings.redis_url:
        return None
    if _redis_client is None:
        _redis_client = Redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
        try:
            await _redis_client.ping()
        except RedisError as exc:
            logger.warning("redis_unavailable_falling_back_to_database", extra={"error": str(exc)})
            _redis_disabled = True
            _redis_client = None
            return None
    return _redis_client


async def _run_redis_operation(operation: Callable[[Redis], Awaitable[None]]) -> None:
    global _redis_client, _redis_disabled
    redis = await get_redis()
    if redis is None:
        return
    try:
        await operation(redis)
    except RedisError as exc:
        logger.warning("redis_operation_failed_falling_back_to_database", extra={"error": str(exc)})
        _redis_disabled = True
        _redis_client = None


async def ensure_slots_for_date(session: AsyncSession, space: Space, target_date: date) -> list[TimeSlot]:
    existing = await session.execute(
        select(TimeSlot).where(TimeSlot.space_id == space.id, TimeSlot.date == target_date).order_by(TimeSlot.start_time)
    )
    slots = list(existing.scalars().all())
    if slots:
        return slots

    weekday = target_date.strftime("%a").lower()[:3]
    hours = (space.operating_hours or {}).get(weekday) or list(_fallback_window(space.type))
    if len(hours) < 2:
        return []

    current = datetime.combine(target_date, time.fromisoformat(hours[0]))
    close_at = datetime.combine(target_date, time.fromisoformat(hours[1]))
    created: list[TimeSlot] = []
    while current < close_at:
        end = current + timedelta(hours=1)
        slot = TimeSlot(
            space_id=space.id,
            date=target_date,
            start_time=current.time(),
            end_time=end.time(),
            status=SlotStatus.available,
        )
        session.add(slot)
        created.append(slot)
        current = end
    await session.commit()
    for slot in created:
        await session.refresh(slot)
    return created


async def sweep_expired_holds(session: AsyncSession) -> int:
    result = await session.execute(
        select(TimeSlot).where(
            TimeSlot.status == SlotStatus.held,
            TimeSlot.held_until.is_not(None),
            TimeSlot.held_until < utc_now(),
        )
    )
    slots = list(result.scalars().all())
    if not slots:
        return 0

    for slot in slots:
        slot.status = SlotStatus.available
        slot.held_by = None
        slot.hold_token = None
        slot.held_until = None

    await session.commit()
    await _run_redis_operation(_delete_slot_keys(slots))
    return len(slots)


def _slots_are_consecutive(slots: list[TimeSlot]) -> bool:
    ordered = sorted(slots, key=lambda slot: slot.start_time)
    for current, nxt in zip(ordered, ordered[1:]):
        if current.end_time != nxt.start_time:
            return False
    return True


async def hold_slots(session: AsyncSession, user: User, space: Space, target_date: date, slot_ids: list[uuid.UUID]) -> dict:
    await ensure_slots_for_date(session, space, target_date)
    await sweep_expired_holds(session)

    result = await session.execute(
        select(TimeSlot)
        .where(TimeSlot.space_id == space.id, TimeSlot.date == target_date, TimeSlot.id.in_(slot_ids))
        .order_by(TimeSlot.start_time)
    )
    slots = list(result.scalars().all())
    if len(slots) != len(slot_ids):
        raise api_error(404, "One or more selected slots were not found", "slot_not_found")
    if not _slots_are_consecutive(slots):
        raise api_error(400, "Selected slots must be consecutive", "invalid_slot_range")

    for slot in slots:
        if slot.status == SlotStatus.booked:
            raise api_error(409, "One of the selected slots is already booked", "slot_booked")
        held_until = normalize_utc(slot.held_until)
        if slot.status == SlotStatus.held and slot.held_by != user.id and held_until and held_until > utc_now():
            raise api_error(409, "One of the selected slots is already held", "slot_held")

    expires_at = utc_now() + timedelta(seconds=settings.hold_duration_seconds)
    hold_id = str(uuid.uuid4())
    total_amount = float(Decimal(str(space.price_per_hour)) * Decimal(len(slots)))
    for slot in slots:
        slot.status = SlotStatus.held
        slot.held_by = user.id
        slot.hold_token = hold_id
        slot.held_until = expires_at

    await session.commit()
    payload = {
        "hold_id": hold_id,
        "space_id": str(space.id),
        "slot_ids": [str(slot.id) for slot in slots],
        "expires_at": expires_at.isoformat(),
        "user_id": str(user.id),
        "amount": total_amount,
    }
    await _run_redis_operation(_store_hold(hold_id, slots, payload))

    return {"hold_id": hold_id, "expires_at": expires_at, "total_amount": total_amount, "slot_ids": slot_ids}


async def get_hold_context(session: AsyncSession, hold_id: str, user_id: uuid.UUID) -> tuple[list[TimeSlot], Space]:
    await sweep_expired_holds(session)
    result = await session.execute(
        select(TimeSlot)
        .options(selectinload(TimeSlot.space))
        .where(TimeSlot.hold_token == hold_id, TimeSlot.held_by == user_id, TimeSlot.status == SlotStatus.held)
        .order_by(TimeSlot.start_time)
    )
    slots = list(result.scalars().all())
    if not slots:
        raise api_error(404, "This slot hold has expired", "hold_expired")
    if any((held_until := normalize_utc(slot.held_until)) is None or held_until < utc_now() for slot in slots):
        raise api_error(409, "This slot hold has expired", "hold_expired")
    return slots, slots[0].space


async def release_hold(session: AsyncSession, hold_id: str) -> None:
    result = await session.execute(select(TimeSlot).where(TimeSlot.hold_token == hold_id))
    slots = list(result.scalars().all())
    for slot in slots:
        if slot.status == SlotStatus.held:
            slot.status = SlotStatus.available
        slot.held_by = None
        slot.hold_token = None
        slot.held_until = None
    await session.commit()

    await _run_redis_operation(_delete_hold(hold_id, slots))


async def create_booking_from_hold(
    session: AsyncSession,
    user: User,
    hold_id: str,
    razorpay_order_id: str | None = None,
    razorpay_payment_id: str | None = None,
    razorpay_signature: str | None = None,
) -> Booking:
    slots, space = await get_hold_context(session, hold_id, user.id)
    booking = Booking(
        user_id=user.id,
        space_id=space.id,
        slot_id=slots[0].id,
        booking_date=slots[0].date,
        start_time=slots[0].start_time,
        end_time=slots[-1].end_time,
        total_amount=float(Decimal(str(space.price_per_hour)) * Decimal(len(slots))),
        status=BookingStatus.confirmed,
        razorpay_order_id=razorpay_order_id,
        razorpay_payment_id=razorpay_payment_id,
        razorpay_signature=razorpay_signature,
    )
    session.add(booking)
    for slot in slots:
        slot.status = SlotStatus.booked
        slot.held_by = None
        slot.hold_token = None
        slot.held_until = None
    await session.commit()
    await session.refresh(booking)
    await release_hold(session, hold_id)
    return booking


async def cancel_booking(session: AsyncSession, booking: Booking, reason: str) -> Booking:
    result = await session.execute(
        select(TimeSlot).where(
            TimeSlot.space_id == booking.space_id,
            TimeSlot.date == booking.booking_date,
            TimeSlot.start_time >= booking.start_time,
            TimeSlot.end_time <= booking.end_time,
        )
    )
    slots = list(result.scalars().all())
    for slot in slots:
        slot.status = SlotStatus.available
        slot.held_by = None
        slot.hold_token = None
        slot.held_until = None

    booking.status = BookingStatus.cancelled
    booking.cancellation_reason = reason
    await session.commit()
    await session.refresh(booking)
    return booking


def _delete_slot_keys(slots: list[TimeSlot]) -> Callable[[Redis], Awaitable[None]]:
    async def operation(redis: Redis) -> None:
        for slot in slots:
            await redis.delete(f"spacebook:slot:{slot.id}")

    return operation


def _store_hold(hold_id: str, slots: list[TimeSlot], payload: dict[str, object]) -> Callable[[Redis], Awaitable[None]]:
    async def operation(redis: Redis) -> None:
        await redis.set(f"spacebook:hold:{hold_id}", json.dumps(payload), ex=settings.hold_duration_seconds)
        for slot in slots:
            await redis.set(f"spacebook:slot:{slot.id}", hold_id, ex=settings.hold_duration_seconds)

    return operation


def _delete_hold(hold_id: str, slots: list[TimeSlot]) -> Callable[[Redis], Awaitable[None]]:
    async def operation(redis: Redis) -> None:
        await redis.delete(f"spacebook:hold:{hold_id}")
        for slot in slots:
            await redis.delete(f"spacebook:slot:{slot.id}")

    return operation
