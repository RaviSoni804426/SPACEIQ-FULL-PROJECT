from __future__ import annotations

from contextlib import asynccontextmanager

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from slowapi.extension import _rate_limit_exceeded_handler

from app.config import settings
from app.database import SessionLocal
from app.routers import analytics, auth, bookings, chat, discovery, partner, payments, reviews, spaces
from app.services.slot_manager import sweep_expired_holds
from app.utils.logging import configure_logging
from app.utils.rate_limit import limiter


@asynccontextmanager
async def lifespan(app: FastAPI):
    scheduler = AsyncIOScheduler()

    async def _sweep() -> None:
        async with SessionLocal() as session:
            await sweep_expired_holds(session)

    scheduler.add_job(_sweep, "interval", seconds=settings.slot_sweep_interval_seconds)
    scheduler.start()
    app.state.scheduler = scheduler
    yield
    scheduler.shutdown(wait=False)


configure_logging(settings.log_level)
app = FastAPI(title=settings.app_name, version="1.0.0", lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(spaces.router)
app.include_router(bookings.router)
app.include_router(payments.router)
app.include_router(chat.router)
app.include_router(discovery.router)
app.include_router(analytics.router)
app.include_router(partner.router)
app.include_router(reviews.router)


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "code": exc.headers.get("X-Error-Code", "http_error") if exc.headers else "http_error"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(status_code=422, content={"detail": str(exc), "code": "validation_error"})


@app.get("/")
async def root() -> dict[str, str]:
    return {"app": settings.app_name, "docs": "/docs", "status": "ok"}


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}
