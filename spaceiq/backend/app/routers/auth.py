from __future__ import annotations

from google.auth.transport import requests as google_requests
from google.oauth2 import id_token
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends

from app.config import settings
from app.database import get_db
from app.models import User, UserRole
from app.schemas import (
    GoogleLoginRequest,
    LoginRequest,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPair,
    UserOut,
)
from app.utils.errors import api_error
from app.utils.security import (
    create_token,
    create_token_pair,
    decode_token,
    get_current_user,
    get_password_hash,
    verify_password,
)


router = APIRouter(prefix="/api/auth", tags=["auth"])


def _normalized_email(email: str) -> str:
    return email.strip().lower()


@router.post("/register", response_model=TokenPair)
async def register(payload: RegisterRequest, session: AsyncSession = Depends(get_db)) -> TokenPair:
    existing = await session.execute(select(User).where(func.lower(User.email) == _normalized_email(payload.email)))
    if existing.scalar_one_or_none():
        raise api_error(400, "Email already exists", "email_exists")

    user = User(
        email=_normalized_email(payload.email),
        hashed_password=get_password_hash(payload.password),
        full_name=payload.full_name.strip(),
        phone=payload.phone,
        role=UserRole.user,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    access_token, refresh_token = create_token_pair(user.id)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/login", response_model=TokenPair)
async def login(payload: LoginRequest, session: AsyncSession = Depends(get_db)) -> TokenPair:
    result = await session.execute(select(User).where(func.lower(User.email) == _normalized_email(payload.email)))
    user = result.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.hashed_password):
        raise api_error(401, "Invalid email or password", "invalid_credentials")

    access_token, refresh_token = create_token_pair(user.id)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/refresh", response_model=TokenPair)
async def refresh(payload: RefreshRequest, session: AsyncSession = Depends(get_db)) -> TokenPair:
    token_payload = decode_token(payload.refresh_token, "refresh")
    user_id = token_payload.get("sub")
    result = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if not user:
        raise api_error(401, "Invalid refresh token", "invalid_refresh_token")

    access_token = create_token(str(user.id), "access", settings.access_token_expire_minutes)
    refresh_token = create_token(str(user.id), "refresh", settings.refresh_token_expire_minutes)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.post("/google", response_model=TokenPair)
async def google_login(payload: GoogleLoginRequest, session: AsyncSession = Depends(get_db)) -> TokenPair:
    if not settings.google_oauth_client_id:
        raise api_error(503, "Google OAuth is not configured", "google_oauth_not_configured")

    try:
        token_info = id_token.verify_oauth2_token(
            payload.id_token,
            google_requests.Request(),
            settings.google_oauth_client_id,
        )
    except Exception as exc:
        raise api_error(401, "Google token verification failed", "invalid_google_token") from exc

    email = _normalized_email(token_info["email"])
    result = await session.execute(select(User).where(func.lower(User.email) == email))
    user = result.scalar_one_or_none()
    if user is None:
        user = User(
            email=email,
            full_name=token_info.get("name", email.split("@")[0].title()),
            avatar_url=token_info.get("picture"),
            google_id=token_info.get("sub"),
            role=UserRole.user,
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)

    access_token, refresh_token = create_token_pair(user.id)
    return TokenPair(access_token=access_token, refresh_token=refresh_token, user=UserOut.model_validate(user))


@router.get("/me", response_model=UserOut)
async def me(user: User = Depends(get_current_user)) -> UserOut:
    return UserOut.model_validate(user)


@router.put("/me", response_model=UserOut)
async def update_me(
    payload: ProfileUpdateRequest,
    session: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> UserOut:
    user.full_name = payload.full_name.strip()
    user.phone = payload.phone
    user.avatar_url = payload.avatar_url
    await session.commit()
    await session.refresh(user)
    return UserOut.model_validate(user)
import uuid
