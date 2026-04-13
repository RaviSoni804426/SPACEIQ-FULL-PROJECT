# SpaceBook Bangalore Build and Deploy Guide

This guide is the fastest reliable path to take the current repo from local MVP to a Bangalore-focused live pilot.

## Launch scope

Recommended day-1 scope:

- coworking spaces
- sports venues
- meeting rooms
- studios

Keep the launch city limited to Bangalore until:

- Google Places sync quality is validated
- partner onboarding is working
- Razorpay payment success and failure flows are tested
- slot holds behave correctly under concurrent usage

## What is already implemented

- Next.js 14 App Router frontend with mobile-ready navigation
- FastAPI backend with async SQLAlchemy and Alembic
- JWT auth with email/password plus Google OAuth frontend and backend flow
- Google Places sync and DB upsert flow
- Redis-backed 5-minute slot holds
- Razorpay order creation and signature verification
- OpenAI-backed chatbot with rule-based fallback
- Partner Hub, Analytics, My Bookings, Account, and review flows

## Production architecture

- Frontend: Vercel
- Backend: Render
- Database: Neon Postgres
- Cache: Upstash Redis
- Search/catalog source: Google Places API
- Payments: Razorpay
- AI assistant: OpenAI `gpt-4o-mini`

## 1. Create infrastructure

### Neon

1. Create a new Neon project.
2. Enable connection pooling.
3. Copy the pooled connection string.
4. Save it for `DATABASE_URL`.

### Upstash Redis

1. Create a Redis database.
2. Copy the TCP URL.
3. Save it for `REDIS_URL`.

### Google Cloud

1. Create a project.
2. Enable:
   - Places API
   - Maps JavaScript API
3. Create:
   - one server key for backend use
   - one browser key for frontend use

Required envs:

- `GOOGLE_PLACES_API_KEY`
- `GOOGLE_OAUTH_CLIENT_ID`
- `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`
- `NEXT_PUBLIC_GOOGLE_MAPS_KEY`

### Razorpay

1. Create an account.
2. Switch to Test Mode first.
3. Copy:
   - `RAZORPAY_KEY_ID`
   - `RAZORPAY_KEY_SECRET`
   - `NEXT_PUBLIC_RAZORPAY_KEY_ID`

### OpenAI

1. Create an API key.
2. Set `OPENAI_API_KEY`
3. Keep `OPENAI_MODEL=gpt-4o-mini`

## 2. Prepare environment variables

Use `spaceiq/.env.example` as the source of truth.

Backend and Docker use:

```text
spaceiq/.env
```

Local Next.js development also needs:

```text
spaceiq/frontend/.env.local
```

Minimum production envs:

- `APP_ENV=production`
- `DEBUG=false`
- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY`
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

## 3. Local validation before deployment

From repo root:

```bash
docker compose up --build
```

Then seed demo users:

```bash
docker compose exec backend python -m app.scripts.seed_demo_users
```

Optional local demo inventory:

```bash
docker compose exec backend python -m app.scripts.seed_demo_inventory
```

QA credentials:

- `test@spacebook.in / Test@123`
- `partner@spacebook.in / Test@123`

Local URLs:

- Frontend: `http://localhost:3000`
- Backend: `http://localhost:8000`
- API docs: `http://localhost:8000/docs`

Local fallback behavior:

- If Redis is unavailable, slot holds continue with the database-backed flow.
- If Google Places is not configured, Partner Hub sync seeds demo Bangalore inventory.
- If Razorpay is not configured, checkout uses a demo payment flow so booking QA still works.

## 4. Seed real Bangalore inventory

Log in as the partner user and use the Partner Hub sync button, or call the API directly with a partner/admin token:

```bash
curl -X POST http://localhost:8000/api/spaces/sync-google \
  -H "Authorization: Bearer <jwt>" \
  -H "Content-Type: application/json" \
  -d '{}'
```

The sync flow:

1. Searches Google Places for Bangalore queries like coworking and sports venues
2. Fetches place details
3. Estimates hourly pricing by locality and type
4. Stores amenities, ratings, images, coordinates, and operating hours
5. Upserts by `google_place_id`

## 5. Deploy backend on Render

### Recommended setup

- Service type: Web Service
- Runtime: Python
- Root directory: `spaceiq/backend`
- Build command:

```bash
pip install -r requirements.txt
```

- Start command:

```bash
bash -lc "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port $PORT"
```

- Health check path: `/health`

### Required backend env vars on Render

- `APP_ENV=production`
- `DEBUG=false`
- `DATABASE_URL=<your neon asyncpg url>`
- `REDIS_URL=<your upstash url>`
- `SECRET_KEY=<strong random value>`
- `ALGORITHM=HS256`
- `ACCESS_TOKEN_EXPIRE_MINUTES=60`
- `REFRESH_TOKEN_EXPIRE_MINUTES=20160`
- `FRONTEND_URL=https://spacebook-blr.vercel.app`
- `ALLOWED_ORIGINS=https://spacebook-blr.vercel.app`
- `GOOGLE_PLACES_API_KEY`
- `GOOGLE_OAUTH_CLIENT_ID`
- `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`
- `NEXT_PUBLIC_GOOGLE_MAPS_KEY`
- `RAZORPAY_KEY_ID`
- `RAZORPAY_KEY_SECRET`
- `NEXT_PUBLIC_RAZORPAY_KEY_ID`
- `OPENAI_API_KEY`

Suggested production backend hostname:

- `https://spacebook-api.onrender.com`

## 6. Deploy frontend on Vercel

### Recommended setup

- Import `spaceiq/frontend`
- Framework: Next.js
- Root directory: `spaceiq/frontend`

### Required frontend env vars on Vercel

- `NEXT_PUBLIC_API_URL=https://spacebook-api.onrender.com`
- `NEXT_PUBLIC_GOOGLE_OAUTH_CLIENT_ID`
- `NEXT_PUBLIC_GOOGLE_MAPS_KEY`
- `NEXT_PUBLIC_RAZORPAY_KEY_ID`

Suggested production frontend hostname:

- `https://spacebook-blr.vercel.app`

## 7. Post-deploy setup

1. Open the frontend.
2. Register or seed the demo users.
3. Promote a user to `partner` or use the seed script.
4. Sync Google Places data.
5. Verify search results are real Bangalore spaces.
6. Run one end-to-end Razorpay test payment.
7. Confirm the booking shows up in My Bookings.
8. Confirm analytics update after confirmed bookings exist.
9. Test SpaceBot with:
   - `Find cheap coworking near HSR`
   - `Book badminton court tomorrow 6pm`

## 8. Go-live checklist

- Frontend deployed on Vercel
- Backend deployed on Render
- Neon and Upstash credentials configured
- Migrations applied on Render
- Google Places sync run successfully
- Razorpay test mode verified
- OpenAI key verified or chatbot fallback accepted
- Partner Hub tested with a real listing
- CORS restricted to the Vercel frontend origin
- Health endpoint and docs checked:
  - `https://spacebook-api.onrender.com/health`
  - `https://spacebook-api.onrender.com/docs`

## 9. Known follow-up upgrades

These are the most valuable next additions after launch readiness:

- direct image uploads via Cloudinary or S3 presigned URLs
- webhook-based Razorpay reconciliation
- recommendation scoring based on booking history and locality affinity

## Official references

- Google Places Text Search: <https://developers.google.com/maps/documentation/places/web-service/text-search>
- Google Place Details: <https://developers.google.com/maps/documentation/places/web-service/details>
- Google Identity Services: <https://developers.google.com/identity/gsi/web/guides/overview>
- Razorpay Python integration: <https://razorpay.com/docs/payments/server-integration/python/integration-steps/>
- Razorpay signature verification: <https://razorpay.com/docs/payments/server-integration/python/integration-steps/#14-verify-payment-signature>
- OpenAI API docs: <https://platform.openai.com/docs/api-reference>
- Vercel Next.js deployment docs: <https://vercel.com/docs/frameworks/nextjs>
- Render Python docs: <https://render.com/docs/deploy-fastapi>
