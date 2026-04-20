from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models import BookingStatus, SlotStatus, SpaceType, UserRole


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserOut(ORMModel):
    id: UUID
    email: EmailStr
    full_name: str
    phone: str | None = None
    avatar_url: str | None = None
    role: UserRole
    created_at: datetime


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: UserOut


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class RefreshRequest(BaseModel):
    refresh_token: str


class ProfileUpdateRequest(BaseModel):
    full_name: str = Field(min_length=2, max_length=120)
    phone: str | None = None
    avatar_url: str | None = None


class TimeSlotOut(ORMModel):
    id: UUID
    date: date
    start_time: time
    end_time: time
    status: SlotStatus
    held_until: datetime | None = None


class SpaceSummary(ORMModel):
    id: UUID
    google_place_id: str | None = None
    name: str
    type: SpaceType
    description: str | None = None
    address: str | None = None
    city: str
    locality: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    price_per_hour: Decimal
    rating: float | None = None
    total_reviews: int
    amenities: list[str]
    images: list[str]
    is_active: bool
    website_url: str | None = None
    phone_number: str | None = None
    source: str
    availability_count: int | None = None


class SpaceDetail(SpaceSummary):
    operating_hours: dict[str, list[str]]
    available_slots: list[TimeSlotOut]


class HoldRequest(BaseModel):
    space_id: UUID
    date: date
    slot_ids: list[UUID] = Field(min_length=1)


class HoldResponse(BaseModel):
    hold_id: str
    expires_at: datetime
    total_amount: float
    slot_ids: list[UUID]
    booking_date: date


class PaymentInitRequest(BaseModel):
    hold_id: str


class PaymentInitResponse(BaseModel):
    order_id: str
    key_id: str
    amount: int
    currency: str = "INR"
    mode: Literal["razorpay", "demo"] = "razorpay"
    hold_id: str
    booking_summary: dict[str, str | float]


class PaymentVerifyRequest(BaseModel):
    hold_id: str
    razorpay_order_id: str
    razorpay_payment_id: str
    razorpay_signature: str


class BookingOut(ORMModel):
    id: UUID
    user_id: UUID
    space_id: UUID
    slot_id: UUID | None = None
    booking_date: date
    start_time: time
    end_time: time
    total_amount: Decimal
    status: BookingStatus
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    cancellation_reason: str | None = None
    created_at: datetime


class BookingCard(BookingOut):
    space_name: str
    locality: str | None = None
    image_url: str | None = None
    review_submitted: bool = False
    review_rating: int | None = None


class BookingCreateRequest(BaseModel):
    hold_id: str
    razorpay_order_id: str | None = None
    razorpay_payment_id: str | None = None
    razorpay_signature: str | None = None


class CancelBookingRequest(BaseModel):
    reason: str = Field(min_length=3, max_length=240)


class ReviewCreateRequest(BaseModel):
    booking_id: UUID
    rating: int = Field(ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class ReviewOut(ORMModel):
    id: UUID
    user_id: UUID
    space_id: UUID
    booking_id: UUID
    rating: int
    comment: str | None = None
    created_at: datetime


class ErrorResponse(BaseModel):
    detail: str
    code: str


class MessageResponse(BaseModel):
    detail: str
    code: str = "ok"
