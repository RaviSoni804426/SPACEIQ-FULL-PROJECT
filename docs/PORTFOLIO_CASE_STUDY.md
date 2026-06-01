# Portfolio Case Study: SpaceIQ AI Revenue Intelligence Platform

## Project Title

SpaceIQ AI Revenue Intelligence Platform

## Elevator Pitch

A production-style booking platform transformed into a data science and AI project that predicts revenue, segments customers, mines review sentiment, and provides an AI assistant for business decisions.

## Industry

PropTech / Space Marketplace (coworking, meeting rooms, studios, sports spaces)

## Problem Statement

Operational booking systems often stop at transaction processing. Product and operations teams still need data-driven answers to questions like:

- Which segments drive most revenue?
- Is growth improving or declining month-over-month?
- Which customer cohorts are at churn risk?
- What are users saying in reviews, and how does sentiment trend?
- What should the business do next?

## My Role and Contributions

- Designed and implemented a reusable analytics service in FastAPI
- Built a forecasting pipeline using historical booking revenue with trend + seasonality adjustments
- Implemented customer segmentation logic (behavior + recency based tiers)
- Added NLP review sentiment and keyword/topic extraction from user feedback
- Created an AI analytics chatbot endpoint with LLM integration and deterministic fallback logic
- Rebuilt the frontend AI dashboard with KPI cards, forecasting, segmentation charts, sentiment view, and interactive chat
- Built reproducible data generation and reporting scripts for portfolio demonstrations

## Architecture Highlights

- Backend: FastAPI + async SQLAlchemy + Pandas analytics pipeline
- Frontend: Next.js + TypeScript + Recharts
- Data layer: SQLite (local), Postgres-ready schema
- AI layer: Groq-compatible LLM endpoint with fallback assistant

## Key Data/AI Features

- Revenue trend analysis (daily/monthly)
- Forecasting (14-day confidence band + 30-day projection)
- KPI system (cancellation rate, repeat customer rate, conversion rate, growth)
- Revenue segmentation (space type and locality)
- Customer tier segmentation (champions, loyal, at-risk, dormant, etc.)
- NLP analysis of review text (sentiment, keywords, topic mentions)
- Business recommendation engine driven by KPI thresholds

## Quantified Outcomes (Current Seeded Dataset)

- Total bookings analyzed: 586
- Successful bookings: 499
- Total revenue: INR 792,363.60
- Avg booking value: INR 1,587.90
- Repeat customer rate: 84.62%
- Search-to-booking conversion: 18.87%
- Forecast confidence: high

## Tech Stack

- Python, FastAPI, Pandas, SQLAlchemy, Alembic
- Next.js 14, TypeScript, Tailwind CSS, Recharts
- SQLite, JWT auth, Razorpay integration
- Groq API (optional)

## GitHub-Ready Repository Sections

- `backend/app/services/analytics.py`: analytics + ML-style logic
- `backend/app/routers/ai.py`: chatbot + analytics API
- `backend/app/scripts/seed_demo_analytics.py`: reproducible historical data generation
- `backend/app/scripts/generate_revenue_report.py`: report generation automation
- `frontend/app/ai/page.tsx`: portfolio dashboard UI
- `docs/REVENUE_ANALYSIS_REPORT.md`: metrics report for stakeholders

## Resume Bullet Ideas

- Built an end-to-end AI analytics platform on top of a production-style booking system, enabling KPI monitoring, customer segmentation, and revenue forecasting.
- Engineered a Pandas-based forecasting and segmentation pipeline that analyzed 586 bookings and projected 30-day revenue with confidence scoring.
- Implemented NLP review mining (sentiment + keyword/topic extraction) to convert unstructured feedback into product insights.
- Developed an AI chatbot for natural-language business querying, supporting both LLM and fallback analytics modes.
- Designed an interactive analytics dashboard in Next.js with multi-chart visualizations for trends, cohorts, and operational performance.