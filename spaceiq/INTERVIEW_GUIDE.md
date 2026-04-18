# SpaceIQ Lite Interview Guide

## 1. 30-Second Pitch

SpaceIQ Lite is a full-stack booking app where users discover spaces, hold hourly slots, complete payment, and track bookings. I built the frontend with Next.js and the backend with FastAPI + async SQLAlchemy. The project is focused, practical, and easy to explain in interviews.

## 2. Problem It Solves

Most demo apps stop at listing data. This project solves the full booking lifecycle:

- find available spaces
- lock slots temporarily
- verify payment on backend
- confirm and manage bookings

## 3. Architecture

```text
Next.js frontend
    |
    | REST APIs
    v
FastAPI backend
    |
    |-- auth
    |-- spaces
    |-- bookings
    |-- payments
    |-- reviews
    |
    v
SQLite (local) / Postgres (production)
```

## 4. Key Tables

- `User`: account, role, profile fields
- `Space`: listing data, pricing, amenities, location
- `TimeSlot`: generated hourly slots by date
- `Booking`: confirmed/cancelled reservations + payment references
- `Review`: post-booking rating/comment

## 4.1 Folder Structure (How to Explain)

- `frontend/app`: route-level pages (explore, booking, account, auth)
- `frontend/components`: UI and reusable feature blocks
- `frontend/hooks`: API-facing hooks (`useSpaces`, `useBookings`, `useAuth`)
- `backend/app/routers`: HTTP layer and request/response contracts
- `backend/app/services`: core business logic (slot hold, payment checks)
- `backend/app/models`: DB entities
- `backend/app/schemas`: validation + response models
- `backend/app/utils`: cross-cutting helpers (security, errors, logging)

## 5. Core Flow You Should Explain

1. User logs in.
2. User searches spaces with filters.
3. User selects consecutive slots.
4. Backend places a temporary hold.
5. Payment is initialized and verified.
6. Hold converts into confirmed booking.
7. User can view/cancel bookings and leave a review.

## 6. Strong Talking Points

- Conflict-safe booking using slot hold + expiry.
- Backend payment verification (not frontend trust).
- Modular backend structure (routers/services/models/schemas).
- Balanced scope: simple enough to ship, deep enough to discuss.

## 7. Common Interview Q&A

### How do you prevent double booking?
Each selected slot is held first. Only valid holds can be converted into confirmed bookings.

### Why verify payments on backend?
Because payment status from frontend can be forged. Signature verification must happen server-side.

### Why is this better than a CRUD project?
It has a real business workflow with validation, concurrency edge cases, and payment confirmation logic.
