# SpaceIQ Lite

SpaceIQ Lite is a simplified full-stack booking project designed for portfolio and resume use.

## What this version focuses on

- User authentication (register/login/profile)
- Space discovery with filters
- Slot hold and conflict-safe booking flow
- Razorpay payment initialization + verification
- Booking history, cancellation, and review submission

## Tech stack

- Frontend: Next.js 14, TypeScript, Tailwind, React Query, Zustand
- Backend: FastAPI, async SQLAlchemy, Alembic
- Database: SQLite (default local), Postgres-ready

## Project structure

```text
spaceiq/
├── frontend/
│   ├── app/             # routes: home, explore, space detail, booking, account, auth
│   ├── components/      # reusable UI + feature components
│   ├── hooks/           # react-query hooks
│   ├── lib/             # api client + utils
│   ├── store/           # auth/ui state (zustand)
│   └── types/           # shared TS types
├── backend/
│   ├── app/
│   │   ├── routers/    # auth, spaces, bookings, payments, reviews
│   │   ├── services/   # slot manager + payment service
│   │   ├── models/
│   │   └── schemas/
│   ├── alembic/
│   └── requirements.txt
└── .env.example
```

## Local setup

1. Copy env:

```bash
cp spaceiq/.env.example spaceiq/.env
```

2. Backend:

```bash
cd spaceiq/backend
pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed_demo_users
python -m app.scripts.seed_demo_inventory
uvicorn app.main:app --reload
```

3. Frontend:

```bash
cd spaceiq/frontend
npm install
npm run dev
```

## Demo credentials

- `test@spaceiq.in` / `Test@123`
- `partner@spaceiq.in` / `Test@123`

## Why this is resume-ready

- Clear end-to-end business flow (search -> hold -> pay -> confirm).
- Good backend design discussion (routers/services/models/schemas separation).
- Includes practical product concerns like slot conflicts and payment verification.

## Interview explanation tip

When explaining structure, use this one-liner:
"Frontend handles user flow and state, backend handles business rules, and database consistency is protected by slot holds + payment verification before booking confirmation."
