# SpaceBook

SpaceBook is a Bangalore-focused space discovery and booking MVP built for fast launch. It combines:

- Next.js 14 App Router frontend
- FastAPI async backend
- PostgreSQL + Alembic
- Redis-backed slot holds
- Google Places sync for real venue data
- Razorpay checkout and signature verification
- OpenAI-powered SpaceBot with fallback intent parsing

The product is designed for coworking spaces, sports venues, studios, and meeting rooms across Bangalore.

## Stack

- Frontend: Next.js 14, Tailwind CSS v3, Zustand, React Query, Recharts, Framer Motion
- Backend: FastAPI, SQLAlchemy async, Alembic, python-jose, Razorpay SDK
- Data: Neon or Supabase Postgres, Upstash Redis
- External APIs: Google Places API, Google Maps JS SDK, Razorpay, OpenAI
- Deployment: Vercel for frontend, Render for backend

## Core product flows

- Explore Bangalore spaces with search, filters, recommendations, and instant result previews
- View real synced place details with map, amenities, and hourly slot availability
- Hold slots for 5 minutes using Redis-backed coordination
- Pay through Razorpay and verify the signature on the backend
- Manage bookings, partner listings, analytics, and profile settings
- Ask SpaceBot to find spaces based on locality, time, budget, and type

## Project structure

```text
spacebook/
├── frontend/         # Next.js 14 app
├── backend/          # FastAPI app, models, routers, services, alembic
├── .env.example      # Shared env template
└── BANGALORE_BUILD_DEPLOY_GUIDE.md
```

## Environment setup

1. Copy the template:

```bash
cp spaceiq/.env.example spaceiq/.env
```

2. For local frontend development, also copy the `NEXT_PUBLIC_*` values into:

```text
spaceiq/frontend/.env.local
```

Important env vars:

- `DATABASE_URL`
- `SECRET_KEY`
- `GOOGLE_PLACES_API_KEY`
- `GOOGLE_OAUTH_CLIENT_ID`
- `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`
- `NEXT_PUBLIC_GOOGLE_MAPS_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `NEXT_PUBLIC_RAZORPAY_KEY_ID`
- `OPENAI_API_KEY`
- `REDIS_URL`
- `NEXT_PUBLIC_API_URL`

## Local development

### One-command Docker setup

From the repo root:

```bash
docker compose up --build
```

This starts:

- Postgres on `localhost:5432`
- Redis on `localhost:6379`
- FastAPI backend on `http://localhost:8000`
- Next.js frontend on `http://localhost:3000`

The backend container runs `alembic upgrade head` automatically before startup.

### Seed demo users

After the stack is running:

```bash
docker compose exec backend python -m app.scripts.seed_demo_users
```

To seed local Bangalore inventory without Google Places credentials:

```bash
docker compose exec backend python -m app.scripts.seed_demo_inventory
```

Demo credentials:

- User: `test@spacebook.in` / `Test@123`
- Partner: `partner@spacebook.in` / `Test@123`

### Seed real Bangalore spaces

Use the Partner Hub after logging in as the partner user, or call the protected sync endpoint:

```bash
curl -X POST http://localhost:8000/api/spaces/sync-google \
  -H "Authorization: Bearer <partner-or-admin-jwt>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

Every synced space comes from Google Places search and place details. No frontend dummy listing data is used.

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

Local development notes:

- If `REDIS_URL` is blank or Redis is unavailable, slot holds still work using the database.
- If Razorpay keys are blank or placeholders, checkout falls back to a demo payment flow.
- If Google Places is not configured, the Partner Hub sync action seeds demo Bangalore inventory.

### Frontend

```bash
cd spaceiq/frontend
npm install
npm run dev
```

## Verified checks completed in this repo

- Frontend lint: `npm run lint`
- Frontend production build: `npm run build`
- Backend import and health smoke test: passed
- Alembic migration upgrade: passed

## Deployment targets

Recommended production names:

- Frontend: `spacebook-blr.vercel.app`
- Backend: `spacebook-api.onrender.com`
- Docs: `spacebook-api.onrender.com/docs`

These URLs are deployment targets, not pre-created live services in this repository. You need your own Vercel, Render, Neon, Upstash, Google, Razorpay, and OpenAI accounts to publish them.

## Deploying the frontend on Vercel

1. Import `spaceiq/frontend` into Vercel as a Next.js project.
2. Add these environment variables:
   - `NEXT_PUBLIC_API_URL`
   - `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`
   - `NEXT_PUBLIC_GOOGLE_MAPS_KEY`
   - `NEXT_PUBLIC_RAZORPAY_KEY_ID`
3. Deploy.

## Deploying the backend on Render

1. Import `spaceiq/backend` as a Python web service or use the included `render.yaml`.
2. Build command:

```bash
pip install -r requirements.txt
```

3. Start command:

```bash
bash -lc "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

4. Add these environment variables in Render:
   - `APP_ENV=production`
   - `DEBUG=false`
   - `DATABASE_URL`
   - `SECRET_KEY`
   - `ALGORITHM=HS256`
   - `ACCESS_TOKEN_EXPIRE_MINUTES=60`
   - `REFRESH_TOKEN_EXPIRE_MINUTES=20160`
   - `FRONTEND_URL`
   - `ALLOWED_ORIGINS`
   - `GOOGLE_PLACES_API_KEY`
   - `GOOGLE_OAUTH_CLIENT_ID`
   - `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`
   - `NEXT_PUBLIC_GOOGLE_MAPS_KEY`
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `NEXT_PUBLIC_RAZORPAY_KEY_ID`
   - `OPENAI_API_KEY`
   - `REDIS_URL`

## Infrastructure setup

### Neon

1. Create a Neon Postgres database.
2. Copy the pooled connection string.
3. Set `DATABASE_URL=postgresql+asyncpg://...`

### Upstash Redis

1. Create a Redis database.
2. Copy the TCP connection string.
3. Set `REDIS_URL=redis://default:password@host:port`

## API key acquisition

### Google Places and Maps

1. Create a Google Cloud project.
2. Enable Places API and Maps JavaScript API.
3. Create server and browser API keys.
4. Use:
   - `GOOGLE_PLACES_API_KEY`
   - `GOOGLE_OAUTH_CLIENT_ID`
   - `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`
   - `NEXT_PUBLIC_GOOGLE_MAPS_KEY`

Official docs:

- https://developers.google.com/maps/documentation/places/web-service/text-search
- https://developers.google.com/maps/documentation/places/web-service/details
- https://developers.google.com/identity/gsi/web/guides/overview

### Razorpay

1. Create a Razorpay account.
2. Switch to Test Mode.
3. Copy:
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `NEXT_PUBLIC_RAZORPAY_KEY_ID`

Official docs:

- https://razorpay.com/docs/payments/server-integration/python/integration-steps/
- https://razorpay.com/docs/payments/server-integration/python/integration-steps/#14-verify-payment-signature

### OpenAI

1. Create an API key in your OpenAI account.
2. Set `OPENAI_API_KEY`
3. Default model: `gpt-4o-mini`

Official docs:

- https://platform.openai.com/docs/models/gpt-4o-mini
- https://platform.openai.com/docs/api-reference

## Go-live checklist

- Add all production env vars in Vercel and Render
- Run backend migrations
- Seed demo users if you want quick QA accounts
- Sync real Bangalore spaces from Google Places
- Complete one full Razorpay test payment
- Verify `/docs`, `/health`, dashboard, booking, partner, analytics, and chat flows

## Notes

- The partner creation flow currently accepts hosted image URLs and stores them directly. If you want direct browser uploads, add Cloudinary or S3 presigned uploads as the next step.
- Google OAuth now works end-to-end when both `GOOGLE_OAUTH_CLIENT_ID` and `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID` are configured.
- SpaceBot uses OpenAI when configured and falls back to keyword-based parsing when the API key is unavailable.
