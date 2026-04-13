from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, model_validator


class ORMModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class BookingWindowModel(BaseModel):
    start_time: datetime
    end_time: datetime

    @model_validator(mode="after")
    def validate_window(self):
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time")
        return self


# Auth
class RegisterRequest(BaseModel):
    name: str
    email: EmailStr
    password: str
    phone: Optional[str] = None


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserOut(ORMModel):
    id: str
    name: str
    email: str
    role: str
    loyalty_pts: int
    phone: Optional[str] = None
    is_admin_requested: bool = False
    created_at: datetime


# Locations
class LocationOut(ORMModel):
    id: str
    name: str
    area: str
    city: str
    address: str
    latitude: Optional[float]
    longitude: Optional[float]
    description: Optional[str]
    amenities: Optional[str]


# Units
class UnitOut(ORMModel):
    id: str
    location_id: str
    name: str
    category: str
    capacity: int
    base_price: float
    description: Optional[str]
    amenities: Optional[str]


# Bookings
class HoldRequest(BookingWindowModel):
    unit_id: str
    source: str = "app"


class HoldResponse(BaseModel):
    held: bool
    price: float
    razorpay_order_id: str
    expires_in_seconds: int = 300


class ConfirmRequest(BookingWindowModel):
    unit_id: str
    amount: float = Field(gt=0)
    order_id: Optional[str] = None
    payment_id: Optional[str] = None
    signature: Optional[str] = None
    source: str = "app"


class BookingOut(ORMModel):
    id: str
    unit_id: str
    unit_name: Optional[str] = None
    location_name: Optional[str] = None
    start_time: datetime
    end_time: datetime
    total_amount: float
    status: str
    source: str
    qr_token: Optional[str] = None
    created_at: datetime


# Reviews
class ReviewRequest(BaseModel):
    unit_id: str
    rating: int = Field(ge=1, le=5)
    comment: Optional[str] = None


class ReviewOut(ORMModel):
    id: str
    unit_id: str
    rating: int
    comment: Optional[str]
    sentiment_score: Optional[float]
    sentiment_label: Optional[str]
    created_at: datetime


# Chat
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None


class ChatResponse(BaseModel):
    reply: str
    action: Optional[str] = None
    options: Optional[List[dict]] = None
    booking: Optional[dict] = None


# Partner / owner onboarding
class OwnerApplicationRequest(BaseModel):
    business_name: str
    business_type: str
    city: str
    phone: Optional[str] = None
    message: Optional[str] = None


class OwnerApplicationOut(ORMModel):
    id: str
    user_id: str
    business_name: str
    business_type: str
    city: str
    phone: Optional[str] = None
    message: Optional[str] = None
    status: str
    review_note: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    created_at: datetime


class ListingSubmissionRequest(BaseModel):
    business_name: str
    business_type: str
    venue_name: str
    category: str
    area: str
    city: str = "Bengaluru"
    address: str
    description: Optional[str] = None
    amenities: Optional[str] = None
    capacity: int = Field(ge=1)
    base_price: float = Field(gt=0)


class ListingSubmissionOut(ORMModel):
    id: str
    user_id: str
    business_name: str
    business_type: str
    venue_name: str
    category: str
    area: str
    city: str
    address: str
    description: Optional[str] = None
    amenities: Optional[str] = None
    capacity: int
    base_price: float
    status: str
    review_note: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_at: Optional[datetime] = None
    approved_location_id: Optional[str] = None
    approved_unit_id: Optional[str] = None
    created_at: datetime


class ReviewDecisionRequest(BaseModel):
    action: str
    note: Optional[str] = None


class BookingReviewRequest(BaseModel):
    action: str
    note: Optional[str] = None


class PartnerDashboardOut(BaseModel):
    pending_owner_applications: int
    pending_listing_submissions: int
    approved_listings: int
    approved_partners: int
