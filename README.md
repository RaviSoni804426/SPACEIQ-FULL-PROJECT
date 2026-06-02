---
title: SpaceIQ AI Revenue Intelligence Platform
emoji: 🏢
colorFrom: indigo
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# SpaceIQ AI Revenue Intelligence Platform

SpaceIQ is a full-stack booking product upgraded into a portfolio-grade Data Science + AI project.

It demonstrates how to transform operational booking data into business intelligence with forecasting, segmentation, NLP, and an AI copilot.

## Core Product

- User authentication and profile management
- Space discovery with filtering (type, locality, price, rating)
- Slot hold and conflict-safe booking flow
- Razorpay payment initialization and verification
- Booking history, cancellation, and reviews

## Data Science + AI Features

- AI analytics chatbot (`/ai/chat`) for KPI interpretation and recommendations
- Revenue analytics engine (`/ai/analytics`) with:
  - Daily and monthly revenue trends
  - 14-day revenue forecasting with confidence band
  - 30-day projected revenue
  - Product and locality revenue segmentation
  - Customer tier segmentation (champions, loyal, at-risk, dormant, etc.)
  - KPI tracking (cancellation rate, repeat rate, search-to-book conversion)
  - NLP sentiment analysis from review text + keyword extraction
- Reproducible analytics dataset seeding (`seed_demo_analytics.py`)
- Auto-generated markdown report (`generate_revenue_report.py`)

## Tech Stack

- Frontend: Next.js 14, TypeScript, Tailwind CSS, Recharts, React Query, Zustand
- Backend: FastAPI, async SQLAlchemy, Alembic, Pandas
- Database: SQLite (default local), Postgres-ready
- AI: Groq (optional), deterministic fallback assistant

## Project Structure

```text
spaceiq-full-project/
├── frontend/
│   ├── app/
│   │   ├── ai/page.tsx               # AI dashboard + chatbot + visual analytics
│   │   └── ...
│   ├── lib/api.ts                    # typed API methods incl. AI endpoints
│   └── types/index.ts                # analytics payload types
├── backend/
│   ├── app/
│   │   ├── routers/ai.py             # chatbot + analytics API
│   │   ├── services/analytics.py     # forecasting, segmentation, NLP pipeline
│   │   └── scripts/
│   │       ├── seed_demo_analytics.py
│   │       └── generate_revenue_report.py
│   └── spaceiq.db
└── docs/
    ├── PORTFOLIO_CASE_STUDY.md
    └── REVENUE_ANALYSIS_REPORT.md
```

## Local Setup

1. Copy environment file

```bash
cp .env.example .env
```

2. Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
python -m app.scripts.seed_demo_users
python -m app.scripts.seed_demo_inventory
python -m app.scripts.seed_demo_analytics --days 210
python -m app.scripts.generate_revenue_report
uvicorn app.main:app --reload
```

3. Frontend

```bash
cd frontend
npm install
npm run dev
```

## Demo Credentials

- `test@spaceiq.in` / `Test@123`
- `partner@spaceiq.in` / `Test@123`

## Hugging Face Spaces Deployment

This repo is ready to deploy as a Docker Space. The root `Dockerfile` builds the Next.js frontend, runs the FastAPI backend, and exposes both through Nginx on port `7860`.

1. Create a new Space on Hugging Face.
2. Choose **Docker** as the Space SDK.
3. Push this repository to the Space repository.
4. In the Space **Settings**, add these variables/secrets:

```text
SECRET_KEY=<strong random string>
GROQ_API_KEY=<optional, for live AI responses>
RAZORPAY_KEY_ID=<optional>
RAZORPAY_KEY_SECRET=<optional secret>
NEXT_PUBLIC_RAZORPAY_KEY_ID=<optional public key>
SEED_DEMO_DATA=true
SEED_ANALYTICS_DAYS=210
FORCE_SEED_ANALYTICS=false
```

The default Space database is SQLite at `/data/spaceiq.db`. A fresh Space seeds demo users, inventory, and analytics automatically. For durable data across restarts, enable Hugging Face persistent storage or switch `DATABASE_URL` to a hosted Postgres database.

## Portfolio Positioning

Use this one-liner in interviews:

"I built a full-stack booking system and extended it into an AI analytics platform with time-series forecasting, customer segmentation, NLP review mining, and a business-facing dashboard with an AI copilot."
