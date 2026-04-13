from __future__ import annotations

import enum
import uuid
from datetime import date, datetime, time

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    Time,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class UserRole(str, enum.Enum):
    user = "user"
    partner = "partner"
    admin = "admin"


class SpaceType(str, enum.Enum):
    coworking = "coworking"
    sports = "sports"
    meeting_room = "meeting_room"
    studio = "studio"


class SlotStatus(str, enum.Enum):
    available = "available"
    held = "held"
    booked = "booked"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str | None] = mapped_column(String(255), nullable=True)
    full_name: Mapped[str] = mapped_column(String(255))
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    avatar_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    google_id: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    role: Mapped[UserRole] = mapped_column(Enum(UserRole, name="user_role"), default=UserRole.user)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owned_spaces: Mapped[list["Space"]] = relationship(back_populates="owner")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="user")
    reviews: Mapped[list["Review"]] = relationship(back_populates="user")


class Space(Base):
    __tablename__ = "spaces"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    google_place_id: Mapped[str | None] = mapped_column(String(255), unique=True, index=True, nullable=True)
    name: Mapped[str] = mapped_column(String(255), index=True)
    type: Mapped[SpaceType] = mapped_column(Enum(SpaceType, name="space_type"))
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    city: Mapped[str] = mapped_column(String(100), default="Bangalore")
    locality: Mapped[str | None] = mapped_column(String(120), index=True, nullable=True)
    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    price_per_hour: Mapped[float] = mapped_column(Numeric(10, 2), default=0)
    rating: Mapped[float | None] = mapped_column(nullable=True)
    total_reviews: Mapped[int] = mapped_column(Integer, default=0)
    amenities: Mapped[list[str]] = mapped_column(JSON, default=list)
    images: Mapped[list[str]] = mapped_column(JSON, default=list)
    operating_hours: Mapped[dict[str, list[str]]] = mapped_column(JSON, default=dict)
    owner_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    source: Mapped[str] = mapped_column(String(60), default="google_places")
    website_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    phone_number: Mapped[str | None] = mapped_column(String(50), nullable=True)
    metadata_json: Mapped[dict[str, str]] = mapped_column("metadata", JSON, default=dict)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    owner: Mapped[User | None] = relationship(back_populates="owned_spaces")
    time_slots: Mapped[list["TimeSlot"]] = relationship(back_populates="space", cascade="all, delete-orphan")
    bookings: Mapped[list["Booking"]] = relationship(back_populates="space")
    reviews: Mapped[list["Review"]] = relationship(back_populates="space")


class TimeSlot(Base):
    __tablename__ = "time_slots"
    __table_args__ = (
        UniqueConstraint("space_id", "date", "start_time", "end_time", name="uq_time_slots_window"),
        Index("ix_time_slots_space_date", "space_id", "date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    space_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("spaces.id", ondelete="CASCADE"))
    date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    status: Mapped[SlotStatus] = mapped_column(Enum(SlotStatus, name="slot_status"), default=SlotStatus.available)
    held_by: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    hold_token: Mapped[str | None] = mapped_column(String(120), nullable=True, index=True)
    held_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    space: Mapped[Space] = relationship(back_populates="time_slots")
    holder: Mapped[User | None] = relationship(foreign_keys=[held_by])


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (Index("ix_bookings_user_created", "user_id", "created_at"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    space_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("spaces.id"))
    slot_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("time_slots.id"), nullable=True)
    booking_date: Mapped[date] = mapped_column(Date)
    start_time: Mapped[time] = mapped_column(Time)
    end_time: Mapped[time] = mapped_column(Time)
    total_amount: Mapped[float] = mapped_column(Numeric(10, 2))
    status: Mapped[BookingStatus] = mapped_column(Enum(BookingStatus, name="booking_status"), default=BookingStatus.pending)
    razorpay_order_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    razorpay_payment_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    razorpay_signature: Mapped[str | None] = mapped_column(String(255), nullable=True)
    cancellation_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="bookings")
    space: Mapped[Space] = relationship(back_populates="bookings")
    slot: Mapped[TimeSlot | None] = relationship()
    review: Mapped["Review | None"] = relationship(back_populates="booking")


class Review(Base):
    __tablename__ = "reviews"
    __table_args__ = (UniqueConstraint("booking_id", name="uq_reviews_booking"),)

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))
    space_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("spaces.id"))
    booking_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("bookings.id"))
    rating: Mapped[int] = mapped_column(Integer)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    user: Mapped[User] = relationship(back_populates="reviews")
    space: Mapped[Space] = relationship(back_populates="reviews")
    booking: Mapped[Booking] = relationship(back_populates="review")


class SearchEvent(Base):
    __tablename__ = "search_events"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    query: Mapped[str] = mapped_column(String(255))
    locality: Mapped[str | None] = mapped_column(String(120), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
