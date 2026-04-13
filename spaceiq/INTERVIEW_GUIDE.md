# SpaceIQ Interview Guide

## 1. Project Pitch

SpaceIQ is an AI-assisted space booking platform built with a Streamlit frontend and a FastAPI backend. It lets users discover spaces, get recommendations, book time slots, receive QR-based access, submit reviews, request admin/partner access, and view analytics.

If you need a one-line intro in the interview, use this:

> SpaceIQ is a full-stack booking system for coworking, sports, and event spaces, with JWT auth, booking orchestration, QR access, chat-assisted search, partner onboarding, and lightweight analytics/ML helpers.

## 2. High-Level Architecture

```text
Streamlit Frontend
    |
    | HTTP/JSON
    v
FastAPI Backend
    |
    |-- Auth layer (JWT)
    |-- Routers (auth, locations, bookings, chat, reviews, analytics, partners, qr)
    |-- Services (booking, qr, sentiment, email, redis, chatbot)
    |-- ML helpers (pricing, recommender, forecasting, anomaly, noshow)
    |
    v
SQLAlchemy ORM
    |
    v
SQLite by default / PostgreSQL-compatible setup

Optional integrations:
- Redis for slot holds and chat session persistence
- Razorpay for payment verification and order creation
- SMTP for email notifications
- Twilio WhatsApp for owner notifications
```

## 3. Tech Stack

- Frontend: Streamlit
- Backend: FastAPI
- ORM: SQLAlchemy
- Database: SQLite by default, PostgreSQL-ready config
- Auth: JWT with `python-jose`
- Password hashing: Passlib with Argon2/Bcrypt
- QR generation: `qrcode`
- Sentiment: VADER with fallback keyword scoring
- Optional infra: Redis, Razorpay, SMTP, Twilio

## 4. Folder Structure

- `frontend/app.py`: full UI, API calls, booking screens, chat UI, analytics UI
- `backend/main.py`: FastAPI app startup and router registration
- `backend/models.py`: database tables/entities
- `backend/schemas.py`: request/response validation
- `backend/auth.py`: password hashing, JWT creation, role checks
- `backend/routers/`: endpoint modules grouped by business domain
- `backend/services/`: reusable business logic and integrations
- `backend/services/ml/`: lightweight prediction/recommendation modules
- `backend/seed_data.py`: creates demo data and sample accounts

## 5. Core Database Entities

### User

Stores user identity, hashed password, role, phone, loyalty points, and admin-request flag.

### Location

Represents a venue/building/brand location such as Smash Arena or The Work Hub.

### Unit

Represents the actual bookable thing inside a location, like a badminton court, meeting room, or hall.

### Booking

Stores the reservation window, amount, source, status, linked user, and linked unit.

### Payment

Stores payment metadata for a booking.

### QRCode

Stores the QR token used for entry validation.

### Review

Stores rating, comment, and sentiment result.

### OwnerApplication

Stores a user's request to become a partner/admin-level operator.

### ListingSubmission

Stores a partner-submitted venue listing waiting for admin approval.

## 6. Request Flow: What Happens Behind the Scenes

### A. User registration/login

1. Frontend sends email and password to `/auth/register` or `/auth/login`.
2. Backend normalizes the email to lowercase.
3. Password is hashed during registration and verified during login.
4. Backend creates a JWT containing the user id in `sub`.
5. Frontend stores the token and sends it in the `Authorization: Bearer ...` header for protected APIs.

### B. Loading the catalog

1. Frontend calls `/locations/`.
2. For each location it calls `/locations/{id}/units`.
3. Backend reads from the database through SQLAlchemy and returns active records.
4. Frontend renders cards, filters, and booking options.

### C. Holding a booking slot

1. Frontend sends `unit_id`, `start_time`, and `end_time` to `/bookings/hold`.
2. Schema validation blocks invalid windows like `end_time <= start_time`.
3. Runtime validation blocks bookings in the past.
4. Backend checks whether the unit exists and is active.
5. Backend checks for overlapping bookings.
6. If Redis exists, it places a short-lived hold to reduce race conditions.
7. Backend calculates dynamic price using base price + occupancy + peak-time signals.
8. Backend returns a price and a demo or Razorpay order id.

### D. Confirming a booking

1. Frontend calls `/bookings/confirm` with the same unit/time window and payment info.
2. Backend optionally verifies Razorpay signature when configured.
3. Shared booking service creates the booking, payment row, QR token, and loyalty points update in one place.
4. Redis hold is released if Redis is active.
5. Backend returns booking id, QR token, and QR image.

### E. QR validation

1. Staff/admin calls `/qr/validate/{token}`.
2. Backend finds the QR record.
3. It rejects invalid, expired, or already-used QR codes.
4. If valid, it marks the QR as used and returns booking/user/unit details.

### F. Chat-assisted booking

1. Frontend sends a natural-language message to `/chat/`.
2. `chatbot_service.py` extracts intent and slot details using deterministic parsing.
3. Backend merges the extracted state with the session state.
4. Search logic queries units from the DB.
5. If the user confirms, the chat route uses the same shared booking service used by the main booking flow.
6. This keeps pricing, QR generation, payment rows, and loyalty logic consistent.

### G. Reviews and sentiment

1. User submits rating and comment to `/reviews/`.
2. Backend checks the user has actually booked the unit.
3. Backend blocks duplicate reviews for the same user/unit pair.
4. If there is a comment, sentiment is computed and stored.

### H. Partner onboarding

1. User submits owner application or listing submission.
2. Admin reviews it from the review queue.
3. If a listing is approved, backend converts the submission into a real `Location` and `Unit`.
4. This is a nice example of a staged moderation workflow.

## 7. ML / Smart Logic Modules

These are intentionally lightweight and interview-friendly.

### Dynamic Pricing

File: `backend/services/ml/pricing.py`

- Input: base price, booking start time, occupancy rate
- Logic:
  - increase price during peak hours
  - increase price on weekends
  - increase price when occupancy is higher
  - slightly decrease price for farther-future bookings
- Output: adjusted price

### Recommender

File: `backend/services/ml/recommender.py`

- Reads the user's confirmed booking history
- Learns favorite categories and usual price range
- Scores active units by category fit + price fit
- Returns top recommendations

### Forecasting

File: `backend/services/ml/forecasting.py`

- Uses historical booking counts per day
- Computes weekday averages and overall average
- Produces future daily demand estimates with lower/upper bounds

### Anomaly Detection

File: `backend/services/ml/anomaly.py`

- Groups bookings by unit and day
- Calculates average and population standard deviation
- Flags unusually high or low demand days using a z-score threshold

### Sentiment

File: `backend/services/sentiment.py`

- Uses VADER when installed
- Falls back to a simple keyword-based scorer if VADER is unavailable

### No-Show Predictor

File: `backend/services/ml/noshow.py`

- Synthetic training example using XGBoost
- Predicts no-show probability from booking behavior features
- Present in the repo as an advanced ML extension, but not wired into the main booking flow yet

## 8. Why This Architecture Works Well

- Clear separation of concerns: routers handle HTTP, services handle business logic, models handle persistence, schemas handle validation.
- Easy to demo: frontend is visually rich and backend is modular.
- Graceful fallbacks: app still works when Redis, Razorpay, SMTP, Twilio, or external LLM services are unavailable.
- Good interview story: shows CRUD, auth, state management, analytics, ML concepts, and operational workflows in one project.

## 9. Important Design Choices You Can Explain

### Why FastAPI?

Because it gives automatic validation, OpenAPI docs, dependency injection, and clean router-based structure.

### Why SQLAlchemy?

Because it maps Python objects to tables cleanly and keeps the database code organized.

### Why JWT?

Because it is stateless and easy for a frontend client to attach on every protected request.

### Why a shared booking service?

Because booking creation was business-critical and duplicated in multiple routes. Centralizing it reduces bugs and keeps booking, payment, QR, and loyalty logic consistent.

### Why optional Redis?

Because it improves slot-hold and session handling, but the project can still run locally without external infrastructure.

### Why lightweight ML instead of heavy production ML?

Because this project is optimized for demoability, explainability, and local execution.

## 10. What I Improved in This Pass

- Added `backend/services/booking_service.py` as the shared source of truth for booking creation.
- Reused the same booking logic in both `/bookings/confirm` and chat-based booking.
- Added stronger request validation in `schemas.py`.
- Blocked past-time booking windows at runtime.
- Prevented duplicate reviews.
- Simplified repeated schema config with a shared ORM base model.
- Modernized `database.py` import usage.

## 11. Interview Questions and Answers

### 1. What problem does SpaceIQ solve?

It solves the problem of discovering and booking spaces quickly while also supporting admin operations, partner onboarding, QR-based entry, and analytics in one system.

### 2. What is the difference between `Location` and `Unit`?

`Location` is the venue or place, while `Unit` is the actual bookable resource inside that place.

### 3. How does authentication work?

The user logs in with email/password, the backend verifies the password hash, creates a JWT, and the frontend sends that JWT on later protected requests.

### 4. Why do you normalize email to lowercase?

To avoid duplicate logical users like `User@x.com` and `user@x.com`.

### 5. How is password security handled?

Plain passwords are never stored. They are hashed using Passlib with Argon2/Bcrypt.

### 6. What is the role of Pydantic schemas?

They validate incoming payloads, shape outgoing responses, and reduce manual validation code in the routes.

### 7. How do you prevent double booking?

The backend checks for overlapping bookings before confirming, and Redis can also place a short hold on the slot.

### 8. Why is Redis optional here?

Because the project should stay runnable on a local laptop. If Redis is unavailable, the app still works with graceful fallback behavior.

### 9. How is dynamic pricing calculated?

It starts from the base price and adjusts using occupancy, peak-hour weight, weekend weight, and days-ahead discounting.

### 10. How does the recommendation engine work?

It looks at the user's past confirmed bookings, detects preferred categories and price level, scores active units, and returns the best matches.

### 11. What happens after a booking is confirmed?

A booking row is created, a payment record is saved, a QR token is generated, loyalty points are updated, and the frontend receives the QR image/token.

### 12. Why generate a QR code?

It gives a simple digital access pass that can be validated at entry without exposing all booking details manually.

### 13. How does QR validation stop misuse?

It rejects invalid, expired, or already-used tokens, and marks a valid token as used after successful validation.

### 14. How does the chat assistant work without a real LLM dependency?

The chatbot service uses deterministic keyword and pattern extraction, so search and booking flows still work even without an external model.

### 15. Why is that a good design choice for this project?

Because it keeps the project reliable for demos and interviews. External AI is optional, not a hard dependency.

### 16. What are the analytics endpoints doing?

They aggregate booking, revenue, user, review, heatmap, forecast, recommendation, and anomaly data for admins.

### 17. How does anomaly detection work?

It compares daily booking counts against each unit's historical average and standard deviation, then flags unusual spikes or dips using z-scores.

### 18. What is partner onboarding?

It is a workflow where users request elevated access and submit venue listings that admins can review and publish.

### 19. Why is the listing submission not published immediately?

Because moderation is important. Review before publish helps with data quality and platform trust.

### 20. How is the frontend connected to the backend?

The Streamlit app uses a shared `api()` helper that attaches JWT headers, sends JSON requests, and handles errors centrally.

### 21. Why did you refactor booking logic into a service?

Because business-critical logic was duplicated across the main booking route and the chat route. Shared logic reduces code and prevents behavioral drift.

### 22. What are current limitations?

SQLite is fine for demo use but not ideal for high concurrency. Redis/Razorpay/SMTP/Twilio are optional and may not be configured locally. The no-show predictor is not yet wired into the live flow.

### 23. How would you scale this project?

Move to PostgreSQL, make Redis mandatory for distributed holds/session state, persist payment-intent state more formally, add background jobs, and split analytics into async processing.

### 24. How would you improve security further?

Add refresh tokens, better secret management, stricter CORS, rate limiting, audit logs, and stronger payment verification rules.

### 25. What was the most important code improvement you made?

Centralizing booking creation into one service, because it reduced duplicate code and made the booking flow more consistent and safer.

## 12. Demo Credentials

Created by `backend/seed_data.py`:

- User: `user1@spaceiq.demo` / `Demo1234!`
- Admin: `admin@spaceiq.demo` / `Admin1234!`
- Owner: `kumarsoniravi705@gmail.com` / `Ravi@123`

## 13. Best Way to Explain the Project in 60 Seconds

SpaceIQ is a full-stack booking platform where users can search spaces, get recommendations, book slots, receive QR access, and leave reviews. The frontend is built in Streamlit, and the backend is a modular FastAPI service with JWT auth, SQLAlchemy models, route-level separation, and reusable service logic. It also includes lightweight ML modules for pricing, recommendations, forecasting, and anomaly detection. I recently cleaned up the booking flow by centralizing booking creation logic into one service so both normal booking and chat-based booking behave consistently.
