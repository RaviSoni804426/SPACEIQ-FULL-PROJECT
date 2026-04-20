from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Callable

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import get_db
from app.models import User, UserRole
from app.utils.errors import api_error


pwd_context = CryptContext(schemes=["argon2", "bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
oauth2_scheme_optional = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str | None) -> bool:
    if not hashed_password:
        return False
    return pwd_context.verify(plain_password, hashed_password)


def create_token(subject: str, token_type: str, expires_minutes: int) -> str:
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=expires_minutes)
    payload = {"sub": subject, "type": token_type, "exp": expires_at}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)


def create_token_pair(user_id: uuid.UUID) -> tuple[str, str]:
    subject = str(user_id)
    access_token = create_token(subject, "access", settings.access_token_expire_minutes)
    refresh_token = create_token(subject, "refresh", settings.refresh_token_expire_minutes)
    return access_token, refresh_token


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError as exc:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials", "invalid_token") from exc
    if payload.get("type") != expected_type:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Token type is invalid", "invalid_token_type")
    return payload


async def get_current_user(
    token: str = Depends(oauth2_scheme),
    session: AsyncSession = Depends(get_db),
) -> User:
    payload = decode_token(token, "access")
    user_id = payload.get("sub")
    if not user_id:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "Could not validate credentials", "missing_subject")
    result = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
    user = result.scalar_one_or_none()
    if user is None:
        raise api_error(status.HTTP_401_UNAUTHORIZED, "User not found", "user_not_found")
    return user


async def get_optional_user(
    token: str | None = Depends(oauth2_scheme_optional),
    session: AsyncSession = Depends(get_db),
) -> User | None:
    if not token:
        return None
    try:
        payload = decode_token(token, "access")
        user_id = payload.get("sub")
        if not user_id:
            return None
        result = await session.execute(select(User).where(User.id == uuid.UUID(user_id)))
        return result.scalar_one_or_none()
    except Exception:
        return None


def require_roles(*roles: UserRole) -> Callable[[User], User]:
    async def dependency(user: User = Depends(get_current_user)) -> User:
        if user.role not in roles:
            raise api_error(status.HTTP_403_FORBIDDEN, "You do not have permission for this action", "forbidden")
        return user

    return dependency
