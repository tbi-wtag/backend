from datetime import datetime, timedelta, timezone
from typing import Optional
import jwt
from pwdlib import PasswordHash
from pwdlib.hashers.bcrypt import BcryptHasher
from fastapi import Request
from fastapi.security import HTTPAuthorizationCredentials
from app.core.config import settings

password_hash = PasswordHash((BcryptHasher(),))


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return password_hash.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    return jwt.encode(
        to_encode, settings.jwt.secret_key, algorithm=settings.jwt.algorithm
    )


def decode_access_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token, settings.jwt.secret_key, algorithms=[settings.jwt.algorithm]
        )
        return payload
    except jwt.PyJWTError:
        return None


def extract_token(request: Request) -> str | None:
    cookie_token = request.cookies.get("access_token")
    if cookie_token:
        return cookie_token.removeprefix("Bearer ").strip()

    auth_header = request.headers.get("Authorization")
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()

    return None
