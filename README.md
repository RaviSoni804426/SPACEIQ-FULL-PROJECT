# SpaceIQ

SpaceIQ is a full-stack Bangalore-focused platform for discovering, booking, and managing coworking spaces, sports venues, studios, and meeting rooms.

It is built to feel like a real product, not just a CRUD demo:

- Next.js 14 App Router frontend
- FastAPI backend with async SQLAlchemy
- Slot hold orchestration with optional Redis acceleration
- Google Places sync for live inventory seeding
- Razorpay checkout and backend payment verification
- OpenAI-assisted search with a rule-based fallback

## Why this project is resume-ready

- It demonstrates complete user journeys: discovery, slot selection, payment, booking history, reviews, and partner inventory management.
- The backend is modular and interview-friendly: routers, services, models, schemas, utilities, and migrations are clearly separated.
- External integrations degrade gracefully, so the app still runs locally without every paid service configured.
- It gives you strong discussion topics around auth, API design, async I/O, state management, payment flows, and product tradeoffs.

## Architecture

```text
Next.js frontend
    |
    | HTTP / JSON
    v
FastAPI backend (`spaceiq/backend/app`)
    |
    |-- Auth and profile management
    |-- Space discovery and Google sync
    |-- Slot holds and booking lifecycle
    |-- Razorpay payment init + verification
    |-- Reviews, partner views, analytics
    |-- AI-assisted search
    |
    v
SQLite locally / Postgres in production

Optional services:
- Redis for faster hold coordination
- Google Places for real Bangalore inventory
- Razorpay for real payments
- OpenAI for richer assistant responses
```

## Active project structure

```text
spaceiq/
├── frontend/              # Next.js 14 application
├── backend/
│   ├── app/               # Active FastAPI application
│   ├── alembic/           # Database migrations
│   ├── data/              # Demo Bangalore inventory seed data
│   ├── requirements.txt
│   └── Dockerfile
├── .env.example
└── INTERVIEW_GUIDE.md
```

## Main product flows

- Search spaces by locality, category, price, rating, and amenities
- Generate hourly slots dynamically from operating hours
- Hold consecutive slots for a short window before checkout
- Initialize and verify payments through Razorpay
- Store confirmed bookings and support cancellations before start time
- Manage partner-owned spaces and partner booking views
- Track recent searches and trending localities
- Ask the AI assistant for space recommendations using natural language

## Quick start

### 1. Configure environment variables

Copy:

```bash
cp spaceiq/.env.example spaceiq/.env
```

For frontend local development, also copy the `NEXT_PUBLIC_*` values into:

```text
spaceiq/frontend/.env.local
```

### 2. Run with Docker

From the repo root:

```bash
docker compose up --build
```

This starts:

- Postgres on `localhost:5432`
- Redis on `localhost:6379`
- FastAPI backend on `http://localhost:8000`
- Next.js frontend on `http://localhost:3000`

### 3. Seed demo accounts

After the stack is running:

```bash
docker compose exec backend python -m app.scripts.seed_demo_users
docker compose exec backend python -m app.scripts.seed_demo_inventory
```

Demo credentials:

- `test@spaceiq.in` / `Test@123`
- `partner@spaceiq.in` / `Test@123`

## Manual local development

### Backend

```bash
cd spaceiq/backend
pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed_demo_users
python -m app.scripts.seed_demo_inventory
uvicorn app.main:app --reload
```

### Frontend

```bash
cd spaceiq/frontend
npm install
npm run dev
```

## Local fallback behavior

- If `REDIS_URL` is blank, slot holds still work through the database.
- If Razorpay keys are blank, checkout falls back to a demo payment flow.
- If Google Places is not configured, the partner sync flow falls back to demo Bangalore inventory.
- If `OPENAI_API_KEY` is missing, the assistant uses deterministic parsing instead of an LLM call.

## Deployment

- Frontend: import `spaceiq/frontend` into Vercel
- Backend: deploy `spaceiq/backend` to Render or another Python host
- Database: Neon / Supabase Postgres or any Postgres-compatible service
- Cache: Upstash Redis or any Redis-compatible service

The included `docker-compose.yml` and `render.yaml` are already aligned with the active app entrypoint: `uvicorn app.main:app`.

## Interview prep

Use [spaceiq/INTERVIEW_GUIDE.md](spaceiq/INTERVIEW_GUIDE.md) for:

- a 30-second project pitch
- architecture explanation
- booking lifecycle walkthrough
- likely interview questions and strong answers
