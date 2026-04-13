from __future__ import annotations

from datetime import date, datetime, time
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator

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


class GoogleLoginRequest(BaseModel):
    id_token: str


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


class SpaceUpsert(BaseModel):
    name: str
    type: SpaceType
    description: str | None = None
    address: str | None = None
    city: str = "Bangalore"
    locality: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    price_per_hour: Decimal = Field(gt=0)
    rating: float | None = None
    total_reviews: int = 0
    amenities: list[str] = Field(default_factory=list)
    images: list[str] = Field(default_factory=list)
    operating_hours: dict[str, list[str]] = Field(default_factory=dict)
    website_url: str | None = None
    phone_number: str | None = None
    is_active: bool = True


class SyncGoogleRequest(BaseModel):
    queries: list[str] = Field(
        default_factory=lambda: [
            "coworking space Bangalore",
            "sports venue Bangalore",
            "meeting room Bangalore",
            "studio rental Bangalore",
        ]
    )


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


class ChatTurn(BaseModel):
    role: Literal["user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    message: str = Field(min_length=2, max_length=800)
    history: list[ChatTurn] = Field(default_factory=list)


class ChatResponse(BaseModel):
    reply: str
    intent: str
    suggested_spaces: list[SpaceSummary] = Field(default_factory=list)


class OverviewStats(BaseModel):
    total_bookings: int
    total_revenue: float
    active_spaces: int
    average_rating: float


class ChartPoint(BaseModel):
    label: str
    value: float


class RevenueBySpacePoint(BaseModel):
    space_name: str
    space_type: SpaceType
    value: float


class RecentSearchOut(BaseModel):
    query: str
    locality: str | None = None
    created_at: datetime


class TrendingLocalityOut(BaseModel):
    locality: str
    space_count: int
    average_price: float


class ErrorResponse(BaseModel):
    detail: str
    code: str


class MessageResponse(BaseModel):
    detail: str
    code: str = "ok"


class SpaceFilters(BaseModel):
    search_query: str | None = None
    type: SpaceType | None = None
    locality: list[str] = Field(default_factory=list)
    price_min: float | None = None
    price_max: float | None = None
    rating: float | None = None
    amenities: list[str] = Field(default_factory=list)
    available_date: date | None = Field(default=None, alias="date")
    sort: str = "relevance"

    @field_validator("sort")
    @classmethod
    def validate_sort(cls, value: str) -> str:
        allowed = {"relevance", "price_asc", "rating", "distance"}
        if value not in allowed:
            return "relevance"
        return value
