# SpaceIQ Interview Guide

## 1. 30-Second Pitch

SpaceIQ is a full-stack booking platform for Bangalore spaces such as coworking hubs, sports venues, studios, and meeting rooms. Users can search spaces, hold slots, complete payments, manage bookings, leave reviews, and use an AI assistant to discover options faster. The frontend is built with Next.js, and the backend is a modular FastAPI service with async SQLAlchemy, optional Redis coordination, Google Places sync, and Razorpay payment verification.

## 2. Problem Statement

Most booking demos stop at simple listings. SpaceIQ focuses on the harder product layer:

- discovery with filters and locality awareness
- temporary slot holds before payment
- payment verification instead of fake success screens
- partner-facing inventory management
- analytics and AI-assisted search

That makes it much easier to discuss in interviews because the project covers real system concerns, not only CRUD.

## 3. High-Level Architecture

```text
Next.js 14 frontend
    |
    | REST APIs
    v
FastAPI backend
    |
    |-- auth router
    |-- spaces router
    |-- bookings router
    |-- payments router
    |-- chat router
    |-- discovery router
    |-- partner router
    |-- analytics router
    |-- reviews router
    |
    v
SQLAlchemy async models
    |
    v
SQLite locally / Postgres in production

Optional integrations:
- Redis
- Google Places API
- Razorpay
- OpenAI
```

## 4. Active Code Structure

- `spaceiq/frontend/`: Next.js App Router UI
- `spaceiq/backend/app/main.py`: app startup, middleware, router registration, scheduler
- `spaceiq/backend/app/models/__init__.py`: database entities
- `spaceiq/backend/app/routers/`: HTTP endpoints grouped by domain
- `spaceiq/backend/app/services/`: booking holds, AI parsing, Google sync, Razorpay logic
- `spaceiq/backend/app/utils/`: auth, rate limiting, logging, serializers, API errors
- `spaceiq/backend/alembic/`: schema migration history

## 5. Core Database Entities

### `User`

Stores identity, hashed password, Google login identity, avatar, and role (`user`, `partner`, `admin`).

### `Space`

Represents a bookable place with type, locality, coordinates, pricing, amenities, images, and owner linkage.

### `TimeSlot`

Represents one-hour bookable windows generated from operating hours for a given date.

### `Booking`

Stores the confirmed reservation window, user, space, total amount, payment references, and cancellation reason.

### `Review`

Stores user feedback attached to a completed booking.

### `SearchEvent`

Stores search intent data used for recent-search and trending-locality views.

## 6. Important Flows You Can Explain

### A. Authentication

1. A user registers or logs in through `/api/auth/register` or `/api/auth/login`.
2. Passwords are hashed before storage.
3. The backend returns an access token and refresh token.
4. The frontend stores the session in Zustand-persisted state.
5. Protected routes use the bearer token for authorization.

### B. Space Discovery

1. The frontend calls `/api/spaces` with filters like locality, rating, price range, and type.
2. The backend queries active `Space` rows and sorts results by relevance, rating, or price.
3. If a search query returns no results, the backend can trigger Google Places sync and retry.
4. Authenticated user searches are stored as `SearchEvent` records.

### C. Slot Hold Before Payment

1. The frontend requests `/api/bookings/hold` with a date and selected slot ids.
2. The backend ensures the slots exist for that date.
3. It validates that the selected slots are consecutive.
4. It blocks already-held or already-booked slots.
5. It marks the chosen slots as held with an expiry timestamp and returns a hold id.

### D. Payment and Booking Confirmation

1. The frontend calls `/api/payments/init` using the hold id.
2. The backend calculates the payable amount and creates a Razorpay order, or a demo order if keys are absent.
3. After checkout, the frontend sends payment details to `/api/payments/verify`.
4. The backend verifies the payment signature.
5. It creates a confirmed booking from the hold and marks the slots as booked.

### E. Reviews

1. Users submit ratings after booking.
2. Reviews are linked to both the booking and the space.
3. This supports richer user trust signals and gives a good relational-model discussion point.

### F. Partner Workflow

1. Partners can create or sync spaces.
2. Partner endpoints return only their owned spaces and their related bookings.
3. Admins can access the broader operational view.

### G. AI Assistant

1. The frontend sends natural-language queries to `/api/chat`.
2. If OpenAI is configured, the backend parses intent through structured model output.
3. If not, a deterministic fallback parser extracts locality, type, and budget.
4. Parsed params are reused to query the same space search logic as the main product flow.

## 7. Design Decisions Worth Discussing

### Why Next.js + FastAPI?

It gives a strong separation between product UI and backend business logic while keeping development fast and interview-friendly.

### Why async SQLAlchemy?

Because the backend talks to multiple external services and performs I/O-heavy work, so async patterns are a good fit.

### Why generate `TimeSlot` rows per date?

It makes hold and booking logic easier to reason about, especially when validating consecutive windows and preventing double booking.

### Why keep Redis optional?

Because the project should still run locally with minimal setup. Redis improves coordination, but it is not a hard blocker for demos.

### Why verify payments on the backend?

Because trust should not depend on frontend state. Razorpay signatures must be verified server-side before confirming a booking.

### Why include fallback behavior for OpenAI and Google Places?

Because demo reliability matters. The app remains usable even when optional APIs are not configured.

## 8. Strong Interview Talking Points

- I separated product concerns cleanly: routes for HTTP, services for business logic, models for persistence, schemas for validation.
- I designed slot holds as a first-class concept so booking conflicts are handled before payment.
- I treated payment verification as a backend responsibility instead of trusting client-side success.
- I used graceful degradation so the project stays demoable without every integration turned on.
- I added partner and analytics surfaces so the project is broader than a single-user booking app.

## 9. Questions You May Get

### How do you prevent double booking?

By holding slot rows before checkout, checking slot status before confirmation, and only converting valid holds into confirmed bookings.

### What happens if Redis is down?

The backend falls back to database-backed hold logic so the product still works locally and during degraded operation.

### How do you keep payment confirmation idempotent?

The payment verification route checks whether a booking already exists for the incoming Razorpay payment id before creating another one.

### What is the role of Google Places here?

It allows the platform to seed or enrich real Bangalore inventory instead of relying only on static demo data.

### Why is this more than a CRUD project?

Because it includes auth, search, stateful slot orchestration, payment verification, partner views, analytics, and AI-assisted intent parsing.

### How would you scale it further?

- move fully to Postgres in production
- make Redis mandatory for distributed locking
- add background jobs for sync and analytics
- add richer audit logs and payment webhooks
- extend partner tools for pricing and inventory operations

## 10. Demo Credentials

- User: `test@spaceiq.in` / `Test@123`
- Partner: `partner@spaceiq.in` / `Test@123`

## 11. Best One-Minute Summary

SpaceIQ is a production-style full-stack booking platform for Bangalore spaces. I built it with a Next.js frontend and a FastAPI backend using async SQLAlchemy. The project supports discovery, slot holds, payment verification, booking history, reviews, partner inventory views, analytics, and an AI assistant. The part I would emphasize in an interview is the booking lifecycle design: generating time slots, holding them temporarily, verifying payment server-side, and only then converting the hold into a confirmed booking.
