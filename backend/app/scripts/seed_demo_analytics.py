from __future__ import annotations

import argparse
import asyncio
import random
from collections import defaultdict
from datetime import date, datetime, time, timedelta

from sqlalchemy import delete, select

from app.database import SessionLocal
from app.models import Booking, BookingStatus, Review, SearchEvent, Space, User, UserRole
from app.utils.security import get_password_hash

POSITIVE_COMMENTS = [
    "Great space with reliable wifi and smooth check-in.",
    "Clean setup and friendly staff. Booking flow was easy.",
    "Excellent value for money. Perfect for team collaboration.",
    "Comfortable environment and good amenities.",
    "Loved the location and overall experience.",
]

NEUTRAL_COMMENTS = [
    "Decent experience overall. Could improve seating comfort.",
    "Good space but parking was a bit tight.",
    "The booking was fine, amenities were average.",
    "Useful for quick meetings, not ideal for long sessions.",
]

NEGATIVE_COMMENTS = [
    "Space was noisy and felt crowded during peak hours.",
    "The experience was average and support was slow.",
    "Price felt high for the facilities provided.",
    "Had minor issues during check-in and service response.",
]

SEARCH_QUERIES = [
    "coworking near metro",
    "meeting room for 6 people",
    "budget workspace bangalore",
    "sports turf evening slot",
    "studio for podcast recording",
    "quiet workspace with wifi",
]


async def _ensure_analytics_users(session, minimum_users: int = 80) -> list[User]:
    users_result = await session.execute(select(User).where(User.role == UserRole.user))
    users = list(users_result.scalars().all())

    if len(users) >= minimum_users:
        return users

    for index in range(len(users) + 1, minimum_users + 1):
        user = User(
            email=f"portfolio_user_{index:02d}@spaceiq.in",
            hashed_password=get_password_hash("Test@123"),
            full_name=f"Portfolio User {index:02d}",
            phone=f"900000{index:04d}",
            role=UserRole.user,
        )
        session.add(user)

    await session.flush()
    users_result = await session.execute(select(User).where(User.role == UserRole.user))
    return list(users_result.scalars().all())


def _weighted_choice(spaces: list[Space]) -> Space:
    # Coworking and meeting spaces are intentionally sampled more often to mimic business demand.
    weighted: list[Space] = []
    for space in spaces:
        if space.type.value == "coworking":
            weighted.extend([space] * 4)
        elif space.type.value == "meeting_room":
            weighted.extend([space] * 3)
        elif space.type.value == "studio":
            weighted.extend([space] * 2)
        else:
            weighted.extend([space] * 2)
    return random.choice(weighted)


def _weighted_user_pool(users: list[User]) -> list[User]:
    ordered_users = sorted(users, key=lambda item: item.email)
    heavy_cutoff = max(1, int(len(ordered_users) * 0.25))
    medium_cutoff = max(heavy_cutoff + 1, int(len(ordered_users) * 0.65))

    heavy = ordered_users[:heavy_cutoff]
    medium = ordered_users[heavy_cutoff:medium_cutoff]
    light = ordered_users[medium_cutoff:]

    weighted: list[User] = []
    weighted.extend(heavy * 8)
    weighted.extend(medium * 3)
    weighted.extend(light * 1)
    return weighted if weighted else ordered_users


def _booking_status(target_day: date, today: date) -> BookingStatus:
    if target_day < today - timedelta(days=2):
        roll = random.random()
        if roll < 0.75:
            return BookingStatus.completed
        if roll < 0.9:
            return BookingStatus.cancelled
        return BookingStatus.confirmed

    if target_day <= today:
        return BookingStatus.confirmed if random.random() < 0.8 else BookingStatus.cancelled

    return BookingStatus.confirmed


def _comment_for_rating(rating: int) -> str:
    if rating >= 4:
        return random.choice(POSITIVE_COMMENTS)
    if rating == 3:
        return random.choice(NEUTRAL_COMMENTS)
    return random.choice(NEGATIVE_COMMENTS)


async def seed_demo_analytics(days: int, reset: bool) -> None:
    random.seed(42)
    today = date.today()

    async with SessionLocal() as session:
        users = await _ensure_analytics_users(session)

        spaces_result = await session.execute(select(Space).where(Space.is_active.is_(True)))
        spaces = list(spaces_result.scalars().all())

        if not users or not spaces:
            raise RuntimeError("Seed users and spaces first: python -m app.scripts.seed_demo_users && python -m app.scripts.seed_demo_inventory")

        weighted_users = _weighted_user_pool(users)

        if reset:
            await session.execute(delete(Review))
            await session.execute(delete(Booking))
            await session.execute(delete(SearchEvent))
            await session.commit()

        created_bookings: list[Booking] = []

        for offset in range(days):
            target_day = today - timedelta(days=(days - offset))

            weekday_factor = 1.2 if target_day.weekday() in {1, 2, 3} else 0.9
            growth_factor = 0.7 + (offset / max(days - 1, 1)) * 0.9
            expected_bookings = max(1.0, 2.2 * weekday_factor * growth_factor)
            booking_count = max(1, int(round(random.gauss(expected_bookings, 1.1))))

            for _ in range(booking_count):
                user = random.choice(weighted_users)
                space = _weighted_choice(spaces)

                start_hour = random.choice([7, 8, 9, 10, 11, 14, 15, 16, 17, 18])
                duration_hours = random.choice([1, 1, 2, 2, 3])
                end_hour = min(start_hour + duration_hours, 22)

                status = _booking_status(target_day, today)
                surge_multiplier = 1.1 if target_day.weekday() in {4, 5} else 1.0
                amount = round(float(space.price_per_hour) * (end_hour - start_hour) * surge_multiplier, 2)

                booking = Booking(
                    user_id=user.id,
                    space_id=space.id,
                    booking_date=target_day,
                    start_time=time(hour=start_hour),
                    end_time=time(hour=end_hour),
                    total_amount=amount,
                    status=status,
                    cancellation_reason=("Schedule change" if status == BookingStatus.cancelled else None),
                    created_at=datetime.combine(target_day, time(hour=max(start_hour - 1, 6))),
                )
                session.add(booking)
                created_bookings.append(booking)

            search_events_count = max(booking_count * random.randint(3, 6), booking_count + 1)
            for _ in range(search_events_count):
                chosen_user = random.choice(users + [None, None])
                locality = random.choice([space.locality or "Bangalore" for space in spaces])
                event = SearchEvent(
                    user_id=chosen_user.id if chosen_user else None,
                    query=random.choice(SEARCH_QUERIES),
                    locality=locality,
                    created_at=datetime.combine(target_day, time(hour=random.randint(7, 21))),
                )
                session.add(event)

        await session.flush()

        ratings_pool = [5, 5, 4, 4, 4, 3, 3, 2]
        space_rating_buckets: defaultdict[str, list[int]] = defaultdict(list)
        review_count = 0
        for booking in created_bookings:
            if booking.status not in {BookingStatus.completed, BookingStatus.confirmed}:
                continue
            if random.random() > 0.42:
                continue

            rating = random.choice(ratings_pool)
            review = Review(
                user_id=booking.user_id,
                space_id=booking.space_id,
                booking_id=booking.id,
                rating=rating,
                comment=_comment_for_rating(rating),
                created_at=datetime.combine(booking.booking_date, time(hour=22, minute=5)),
            )
            session.add(review)
            space_rating_buckets[str(booking.space_id)].append(rating)
            review_count += 1

        await session.flush()

        for space in spaces:
            ratings = space_rating_buckets.get(str(space.id), [])
            if ratings:
                space.total_reviews = len(ratings)
                space.rating = round(sum(ratings) / len(ratings), 2)

        await session.commit()

        status_summary: defaultdict[str, int] = defaultdict(int)
        for booking in created_bookings:
            status_summary[booking.status.value] += 1

        print("Demo analytics dataset generated.")
        print(f"Bookings created: {len(created_bookings)}")
        print(f"Reviews created: {review_count}")
        print(f"Status breakdown: {dict(status_summary)}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed historical bookings, reviews, and searches for analytics demos.")
    parser.add_argument("--days", type=int, default=180, help="Number of historical days to generate")
    parser.add_argument("--no-reset", action="store_true", help="Append data instead of clearing current bookings/reviews/searches")
    args = parser.parse_args()

    asyncio.run(seed_demo_analytics(days=max(args.days, 30), reset=not args.no_reset))


if __name__ == "__main__":
    main()
