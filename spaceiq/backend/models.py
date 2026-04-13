import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime,
    ForeignKey, Text, Enum as SAEnum
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from database import Base
import enum


def gen_uuid():
    return str(uuid.uuid4())


class UserRole(str, enum.Enum):
    user = "user"
    admin = "admin"
    owner = "owner"


class BookingStatus(str, enum.Enum):
    pending = "pending"
    confirmed = "confirmed"
    cancelled = "cancelled"
    completed = "completed"


class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, default=gen_uuid)
    email = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(SAEnum(UserRole), default=UserRole.user)
    is_admin_requested = Column(Boolean, default=False)
    loyalty_pts = Column(Integer, default=0)
    phone = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    bookings = relationship("Booking", back_populates="user")
    reviews = relationship("Review", back_populates="user")


class Location(Base):
    __tablename__ = "locations"

    id = Column(String, primary_key=True, default=gen_uuid)
    name = Column(String, nullable=False)
    area = Column(String, nullable=False)
    city = Column(String, default="Bengaluru")
    address = Column(Text, nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    description = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)  # comma-separated
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    units = relationship("Unit", back_populates="location")


class Unit(Base):
    __tablename__ = "units"

    id = Column(String, primary_key=True, default=gen_uuid)
    location_id = Column(String, ForeignKey("locations.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)  # sports, coworking, events, studio, parking
    capacity = Column(Integer, default=1)
    base_price = Column(Float, nullable=False)
    description = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    location = relationship("Location", back_populates="units")
    bookings = relationship("Booking", back_populates="unit")
    reviews = relationship("Review", back_populates="unit")


class Booking(Base):
    __tablename__ = "bookings"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(SAEnum(BookingStatus), default=BookingStatus.pending)
    source = Column(String, default="app")  # app or chatbot
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="bookings")
    unit = relationship("Unit", back_populates="bookings")
    payment = relationship("Payment", back_populates="booking", uselist=False)
    qr_code = relationship("QRCode", back_populates="booking", uselist=False)


class Payment(Base):
    __tablename__ = "payments"

    id = Column(String, primary_key=True, default=gen_uuid)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False)
    razorpay_order_id = Column(String, nullable=True)
    razorpay_payment_id = Column(String, nullable=True)
    amount = Column(Float, nullable=False)
    status = Column(String, default="pending")  # pending, success, failed
    created_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="payment")


class QRCode(Base):
    __tablename__ = "qr_codes"

    id = Column(String, primary_key=True, default=gen_uuid)
    booking_id = Column(String, ForeignKey("bookings.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)
    is_used = Column(Boolean, default=False)
    expires_at = Column(DateTime, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    booking = relationship("Booking", back_populates="qr_code")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    unit_id = Column(String, ForeignKey("units.id"), nullable=False)
    rating = Column(Integer, nullable=False)  # 1-5
    comment = Column(Text, nullable=True)
    sentiment_score = Column(Float, nullable=True)  # VADER compound
    sentiment_label = Column(String, nullable=True)  # positive/negative/neutral
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="reviews")
    unit = relationship("Unit", back_populates="reviews")


class OwnerApplication(Base):
    __tablename__ = "owner_applications"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    city = Column(String, nullable=False)
    phone = Column(String, nullable=True)
    message = Column(Text, nullable=True)
    status = Column(String, default="pending")
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class ListingSubmission(Base):
    __tablename__ = "listing_submissions"

    id = Column(String, primary_key=True, default=gen_uuid)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    business_name = Column(String, nullable=False)
    business_type = Column(String, nullable=False)
    venue_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    area = Column(String, nullable=False)
    city = Column(String, default="Bengaluru")
    address = Column(Text, nullable=False)
    description = Column(Text, nullable=True)
    amenities = Column(Text, nullable=True)
    capacity = Column(Integer, default=1)
    base_price = Column(Float, nullable=False)
    status = Column(String, default="pending")
    review_note = Column(Text, nullable=True)
    reviewed_by = Column(String, ForeignKey("users.id"), nullable=True)
    reviewed_at = Column(DateTime, nullable=True)
    approved_location_id = Column(String, ForeignKey("locations.id"), nullable=True)
    approved_unit_id = Column(String, ForeignKey("units.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
