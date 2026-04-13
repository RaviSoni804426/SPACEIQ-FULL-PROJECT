"""
Seed the database with synthetic SpaceIQ data.
Run: python seed_data.py
Generates: 3 locations, 10 units each, 180 days of bookings, users, reviews.
"""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from database import SessionLocal, engine
from models import Base, User, Location, Unit, Booking, Payment, QRCode, Review, BookingStatus
from auth import hash_password
from services.qr_service import generate_qr_token
import random
from datetime import datetime, timedelta
import uuid

# Drop all existing tables and recreate
Base.metadata.drop_all(bind=engine)
Base.metadata.create_all(bind=engine)
db = SessionLocal()

random.seed(42)

LOCATIONS = [
    {"name": "Smash Arena", "area": "Koramangala", "address": "5th Block, Koramangala, Bengaluru 560095"},
    {"name": "The Work Hub", "area": "Indiranagar", "address": "100 Feet Road, Indiranagar, Bengaluru 560038"},
    {"name": "Event Forge", "area": "HSR Layout", "address": "Sector 7, HSR Layout, Bengaluru 560102"},
]

UNIT_TEMPLATES = {
    "sports": [
        ("Badminton Court A", 2, 480),
        ("Badminton Court B", 2, 480),
        ("Squash Court", 2, 600),
        ("Table Tennis Room", 4, 300),
    ],
    "coworking": [
        ("Hot Desk", 1, 200),
        ("Private Cabin", 4, 800),
        ("Meeting Room", 8, 1200),
    ],
    "events": [
        ("Main Hall", 100, 5000),
        ("Terrace Space", 50, 3000),
        ("Board Room", 20, 2000),
    ],
}

print("Seeding locations and units...")
all_units = []
for loc_data in LOCATIONS:
    loc = Location(
        id=str(uuid.uuid4()),
        name=loc_data["name"],
        area=loc_data["area"],
        city="Bengaluru",
        address=loc_data["address"],
        latitude=12.9716 + random.uniform(-0.05, 0.05),
        longitude=77.5946 + random.uniform(-0.05, 0.05),
        description=f"Premium {loc_data['area']} space for all your needs.",
    )
    db.add(loc)
    db.flush()

    # Assign categories based on location index
    cat = list(UNIT_TEMPLATES.keys())[LOCATIONS.index(loc_data)]
    for uname, cap, price in UNIT_TEMPLATES[cat]:
        unit = Unit(
            id=str(uuid.uuid4()),
            location_id=loc.id,
            name=uname,
            category=cat,
            capacity=cap,
            base_price=float(price),
        )
        db.add(unit)
        db.flush()
        all_units.append(unit)

print(f"Created {len(all_units)} units across {len(LOCATIONS)} locations.")

# Create users
print("Seeding users...")
users = []
for i in range(20):
    u = User(
        id=str(uuid.uuid4()),
        name=f"User {i+1}",
        email=f"user{i+1}@spaceiq.demo",
        hashed_password=hash_password("Demo1234!"),
        loyalty_pts=random.randint(0, 500),
    )
    db.add(u)
    users.append(u)

# Create owner (super-admin)
owner = User(
    id=str(uuid.uuid4()),
    name="Super Admin",
    email="kumarsoniravi705@gmail.com",
    hashed_password=hash_password("Ravi@123"),
    role="owner",
    loyalty_pts=2000,
)
db.add(owner)

# Create admin
admin = User(
    id=str(uuid.uuid4()),
    name="Admin",
    email="admin@spaceiq.demo",
    hashed_password=hash_password("Admin1234!"),
    role="admin",
    loyalty_pts=1000,
)
db.add(admin)
db.flush()

# Create bookings (180 days of synthetic data)
print("Seeding bookings (180 days)...")
start_date = datetime.utcnow() - timedelta(days=180)
booking_count = 0
for day_offset in range(180):
    day = start_date + timedelta(days=day_offset)
    daily_bookings = random.randint(2, 12)
    for _ in range(daily_bookings):
        unit = random.choice(all_units)
        user = random.choice(users)
        hour = random.choice([8, 9, 10, 11, 14, 15, 16, 17, 18, 19, 20])
        start = day.replace(hour=hour, minute=0, second=0, microsecond=0)
        end = start + timedelta(hours=random.choice([1, 2]))
        amount = unit.base_price * random.uniform(0.9, 1.5)

        booking = Booking(
            id=str(uuid.uuid4()),
            user_id=user.id,
            unit_id=unit.id,
            start_time=start,
            end_time=end,
            total_amount=round(amount, 2),
            status=BookingStatus.confirmed,
            source=random.choice(["app", "chatbot"]),
            created_at=start - timedelta(days=random.randint(0, 7)),
        )
        db.add(booking)
        db.flush()

        payment = Payment(
            id=str(uuid.uuid4()),
            booking_id=booking.id,
            razorpay_payment_id=f"pay_demo_{uuid.uuid4().hex[:12]}",
            amount=booking.total_amount,
            status="success",
        )
        db.add(payment)

        token = generate_qr_token(booking.id)
        qr = QRCode(
            id=str(uuid.uuid4()),
            booking_id=booking.id,
            token=token,
            expires_at=end + timedelta(minutes=15),
        )
        db.add(qr)
        booking_count += 1

print(f"Created {booking_count} bookings.")

# Create reviews
print("Seeding reviews...")
reviews_data = [
    (5, "Absolutely loved this space! Great facilities and very clean."),
    (4, "Good experience overall, minor issues with lighting."),
    (5, "Best badminton court in Bengaluru! Highly recommend."),
    (3, "Average. Could improve the changing rooms."),
    (5, "Booked through the chatbot in 2 minutes. Amazing!"),
    (4, "Nice coworking space, fast WiFi, good coffee."),
    (2, "The AC wasn't working. Staff was unresponsive."),
    (5, "Perfect venue for our team event. Will book again!"),
]
for unit in all_units[:6]:
    for rating, comment in random.sample(reviews_data, 3):
        review = Review(
            id=str(uuid.uuid4()),
            user_id=random.choice(users).id,
            unit_id=unit.id,
            rating=rating,
            comment=comment,
        )
        db.add(review)

db.commit()
print("\n✅ Seed complete!")
print("Admin login: admin@spaceiq.demo / Admin1234!")
print("User login:  user1@spaceiq.demo  / Demo1234!")
